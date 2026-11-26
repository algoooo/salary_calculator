import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from itertools import groupby

from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from sqlalchemy import Date, cast, update

from telegram_bot.classes.states import UpdateWorkdayState
from telegram_bot.keyboards.keyboard_tools import construct_table_keyboard
from telegram_bot.texts.answers import answer
from database import WorkDay
from database.crud import users, workdays
from database.models import User, WorkdayPaidStatus
from database.session import get_session_factory
from tools.pagination import paginate
from tools.parse_message import parse_message

router = Router()
REPORT_DATE = r"(?im)^\s*(дата|когда|день)(?:\s|:)"
SUMMARY_DATE = r"[0-9]{1,2}\.[0-9]{1,2}(?:\.[0-9]{4})?"
SUMMARY_RANGE = re.compile(
    rf"^\s*({SUMMARY_DATE})(?:\s*[-–—]\s*({SUMMARY_DATE}))?(?:[ \t]+(оплачено))?\s*$",
    re.IGNORECASE,
)


class WorkdayAction(CallbackData, prefix="day"):
    action: str
    page: int
    day_id: int = 0


class UnpaidWorkdayAction(WorkdayAction, prefix="unpaid_day"):
    pass


def _week_start(day: WorkDay) -> date:
    work_date = day.workday_date.date()
    return work_date - timedelta(days=work_date.weekday())


async def _show_workdays(
    message: types.Message, user_id: int, page: int, *, edit: bool, unpaid_only: bool = False
):
    action_type = UnpaidWorkdayAction if unpaid_only else WorkdayAction
    pay_status = WorkdayPaidStatus.UNPAID if unpaid_only else None
    async with get_session_factory().begin() as session:
        user = await users.get_user(session, user_id)
        if user is None:
            await message.answer(answer("questions.not_registered"))
            return
        days = await workdays.get_user_workdays(session, user_id, pay_status=pay_status)

    days.sort(key=lambda day: (day.workday_date, day.id), reverse=True)
    weeks = [(start, list(entries)) for start, entries in groupby(days, key=_week_start)]
    selected, page, page_count = paginate(weeks, page, 1)
    heading = answer("workdays.no_unpaid_workdays" if unpaid_only else "workdays.no_workdays_found")
    entries = []
    if selected:
        start, entries = selected[0]
        end = start + timedelta(days=6)
        heading = answer(
            "workdays.unpaid_list" if unpaid_only else "workdays.list",
            start=start.strftime("%d.%m.%Y"),
            end=end.strftime("%d.%m.%Y"),
            page=page + 1,
            pages=page_count,
        )

    buttons = [
        [[answer("workdays.entry", plain=True, date=day.workday_date.strftime("%d.%m.%Y"),
                 place=day.workplace_name),
          action_type(action="view", page=page, day_id=day.id).pack()]]
        for day in reversed(entries)
    ]

    navigation = []
    if page > 0:
        navigation.append([answer("workdays.previous"), action_type(action="list", page=page - 1).pack()])
    if page + 1 < page_count:
        navigation.append([answer("workdays.next"), action_type(action="list", page=page + 1).pack()])
    if navigation:
        buttons.append(navigation)

    send = message.edit_text if edit else message.answer
    if not unpaid_only:
        heading = f"{heading}\n\n{answer('workdays.add_hint')}\n{answer('workdays.summary_hint')}"
    await send(heading, reply_markup=construct_table_keyboard(buttons) if buttons else None)


@router.callback_query(F.data.in_({"my_workdays", "my_unpaid_workdays"}))
async def my_workdays(callback: types.CallbackQuery):
    await callback.answer()
    if isinstance(callback.message, types.Message):
        await _show_workdays(
            callback.message, callback.from_user.id, 0,
            edit=False, unpaid_only=callback.data == "my_unpaid_workdays",
        )


@router.callback_query(WorkdayAction.filter(F.action == "list"))
@router.callback_query(UnpaidWorkdayAction.filter(F.action == "list"))
async def workday_page(callback: types.CallbackQuery, callback_data: WorkdayAction):
    await callback.answer()
    if isinstance(callback.message, types.Message):
        await _show_workdays(
            callback.message, callback.from_user.id, callback_data.page,
            edit=True, unpaid_only=isinstance(callback_data, UnpaidWorkdayAction),
        )


@router.callback_query(WorkdayAction.filter(F.action.in_({"view", "confirm", "delete", "paid", "unpaid"})))
@router.callback_query(UnpaidWorkdayAction.filter(F.action.in_({"view", "confirm", "delete", "paid", "unpaid"})))
async def manage_workday(callback: types.CallbackQuery, callback_data: WorkdayAction):
    await callback.answer()
    message = callback.message
    if not isinstance(message, types.Message):
        return

    user_id = callback.from_user.id
    action = callback_data.action
    day_id = callback_data.day_id
    page = callback_data.page
    action_type = type(callback_data)
    async with get_session_factory().begin() as session:
        if action == "delete":
            deleted = await workdays.delete_workday(session, day_id, user_id)
        elif action in {"paid", "unpaid"}:
            status = WorkdayPaidStatus[action.upper()]
            day = await workdays.update_workday(session, day_id, user_id, pay_status=status)
        else:
            day = await workdays.get_workday(session, day_id, telegram_id=user_id)

    if action == "delete":
        if not deleted:
            await message.answer(answer("workdays.missing"))
        await _show_workdays(
            message, user_id, page, edit=True, unpaid_only=isinstance(callback_data, UnpaidWorkdayAction),
        )
        return

    back = [answer("workdays.back"), action_type(action="list", page=page).pack()]
    if day is None:
        await message.edit_text(answer("workdays.missing"), reply_markup=construct_table_keyboard([[back]]))
        return

    if action == "confirm":
        delete = action_type(action="delete", page=page, day_id=day_id).pack()
        view = action_type(action="view", page=page, day_id=day_id).pack()
        await message.edit_text(
            answer("workdays.confirm_delete"),
            reply_markup=construct_table_keyboard([
                [[answer("workdays.delete"), delete]],
                [[answer("workdays.cancel"), view]],
            ]),
        )
        return

    paid = day.pay_status == WorkdayPaidStatus.PAID
    status_key = "paid" if paid else "unpaid"
    next_status = "unpaid" if paid else "paid"
    status_action = action_type(action=next_status, page=page, day_id=day_id).pack()
    confirm = action_type(action="confirm", page=page, day_id=day_id).pack()
    await message.edit_text(
        answer("workdays.details", date=day.workday_date.strftime("%d.%m.%Y"),
               place=day.workplace_name, hours=day.hours_formatted, total_hours=day.total_hours,
               sales=day.total_profit, salary=day.employee_profit, status=answer(f"workdays.{status_key}")),
        reply_markup=construct_table_keyboard([
            [[answer(f"workdays.mark_{next_status}"), status_action]],
            [[answer("workdays.edit_pay"), action_type(action="edit_pay", page=page, day_id=day_id).pack()]],
            [[answer("workdays.delete"), confirm]],
            [back],
        ]),
    )


@router.callback_query(WorkdayAction.filter(F.action == "edit_pay"))
@router.callback_query(UnpaidWorkdayAction.filter(F.action == "edit_pay"))
async def edit_workday_pay(callback: types.CallbackQuery, callback_data: WorkdayAction, state: FSMContext):
    await callback.answer()
    if not isinstance(callback.message, types.Message):
        return

    async with get_session_factory().begin() as session:
        day = await workdays.get_workday(session, callback_data.day_id, telegram_id=callback.from_user.id)
    if day is None:
        await callback.message.answer(answer("workdays.missing"))
        return

    await state.clear()
    await state.update_data(workday_id=day.id)
    await state.set_state(UpdateWorkdayState.Enter_pay_rates)
    await callback.message.answer(answer("workdays.enter_pay_rates", date=day.workday_date.strftime("%d.%m.%Y")))


@router.message(UpdateWorkdayState.Enter_pay_rates)
async def save_workday_pay(message: types.Message, state: FSMContext):
    rates = re.fullmatch(r"\s*([0-9]{1,10})\s+([0-9]{1,3})\s*", message.text or "")
    if rates is None or int(rates[2]) > 100:
        await message.answer(answer("workdays.invalid_pay_rates"))
        return

    hourly_rate, sales_percent = map(int, rates.groups())
    data = await state.get_data()
    user_id = message.from_user.id
    async with get_session_factory().begin() as session:
        day = await workdays.get_workday(session, data["workday_id"], telegram_id=user_id)
        if day is not None:
            salary = round(
                day.total_hours * hourly_rate + Decimal(str(day.total_profit)) * sales_percent / 100,
                2,
            )
            day = await workdays.update_workday(session, day.id, user_id, employee_profit=float(salary))

    await state.clear()
    if day is None:
        await message.answer(answer("workdays.missing"))
        return
    await message.answer(answer("workdays.pay_updated", salary=day.employee_profit))


def _summary_date(value: str, year: int) -> date:
    if value.count(".") == 1:
        value = f"{value}.{year}"
    return datetime.strptime(value, "%d.%m.%Y").date()


@router.message(StateFilter(None), F.text.regexp(SUMMARY_RANGE).as_("date_range"))
async def show_workday_summary(message: types.Message, date_range: re.Match[str]):
    first, last, mark_paid = date_range.groups()
    year = date.today().year
    try:
        start = _summary_date(first, year)
        end = _summary_date(last, year) if last is not None else start
        if end < start:
            raise ValueError("End date precedes start date")
    except ValueError:
        await message.answer(answer("workdays.summary_invalid"))
        return

    period = {"start": start.strftime("%d.%m.%Y"), "end": end.strftime("%d.%m.%Y")}
    async with get_session_factory().begin() as session:
        user_id = message.from_user.id
        user = await users.get_user(session, user_id)
        if user is not None:
            if mark_paid:
                updated = await session.scalars(
                    update(WorkDay)
                    .where(
                        WorkDay.employee_id == user_id,
                        cast(WorkDay.workday_date, Date).between(start, end),
                        WorkDay.pay_status == WorkdayPaidStatus.UNPAID,
                    )
                    .values(pay_status=WorkdayPaidStatus.PAID)
                    .returning(WorkDay.id)
                )
                paid_count = len(updated.all())
            else:
                days = await workdays.get_user_workdays(session, user_id)

    if user is None:
        await message.answer(answer("questions.not_registered"))
        return
    if mark_paid:
        key = "workdays.range_paid" if paid_count else "workdays.range_no_unpaid"
        await message.answer(answer(key, **period, shifts=paid_count))
        return

    days = [day for day in days if start <= day.workday_date.date() <= end]
    if not days:
        await message.answer(answer("workdays.summary_empty", **period))
        return

    salary = sum(day.employee_profit for day in days)
    paid = sum(day.employee_profit for day in days if day.pay_status == WorkdayPaidStatus.PAID)
    await message.answer(answer(
        "workdays.summary",
        **period,
        shifts=len(days),
        hours=sum(day.total_hours for day in days),
        sales=sum(day.total_profit for day in days),
        salary=salary,
        paid=paid,
        unpaid=salary - paid,
    ))


@router.message(StateFilter(None), F.text.regexp(REPORT_DATE))
@router.message(StateFilter(None), F.caption.regexp(REPORT_DATE))
async def add_workday(message: types.Message):
    report_text = message.text or message.caption or ""
    try:
        day = parse_message(report_text)
        if day.place_name in {"", "ERROR"} or day.hours <= 0 or min(
            day.total_profit, day.total_by_cash, day.total_by_card, day.total_by_transfer
        ) < 0:
            raise ValueError("Incomplete workday report")
    except Exception:
        # The existing parser also raises plain Exception for invalid dates and times.
        await message.answer(answer("workdays.invalid"))
        return

    result = "questions.not_registered"
    async with get_session_factory().begin() as session:
        # Serialize report submissions for this employee until the insert commits.
        user = await session.get(User, message.from_user.id, with_for_update=True)
        if user is not None:
            days = await workdays.get_user_workdays(session, user.telegram_id)
            workplace = day.place_name.strip().casefold()
            duplicate = any(
                saved.workday_date.date() == day.date.date()
                and saved.workplace_name.strip().casefold() == workplace
                for saved in days
            )
            result = "workdays.duplicate" if duplicate else "workdays.added"
        if result == "workdays.added":
            employee_profit = round(
                day.hours * (user.salary_per_hour or 0)
                + day.total_profit * (user.sales_percent or 0) / 100,
                2,
            )
            await workdays.create_workday(
                session,
                employee_id=user.telegram_id,
                date=day.date,
                place=day.place_name,
                total_hours=day.hours,
                formatted_hours=day.hours_formatted,
                employee_profit=employee_profit,
                total_profit=day.total_profit,
                by_card=day.total_by_card,
                by_cash=day.total_by_cash,
                by_transfer=day.total_by_transfer,
                shortage=None if day.shortage == -1000 else day.shortage,
            )

    await message.answer(answer(result))
