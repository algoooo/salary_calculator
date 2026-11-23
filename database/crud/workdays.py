from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import WorkDay


async def _owned_workdays(session: AsyncSession, workday_id: int, user_id: int) -> WorkDay | None:
    return await session.scalar(select(WorkDay).where(
        WorkDay.id == workday_id, WorkDay.employee_id == user_id
    ))


async def get_workdays_by_date(
        session: AsyncSession,
        user_id: int,
        dates: list[datetime]
) -> list[WorkDay] | None:

    workdays = []

    for date in dates:
        item: WorkDay | None = await session.scalar(select(WorkDay).where(WorkDay.workday_date == date))

        if item is None:
            continue

        actual_workday = await get_workday(session, item.id, telegram_id=user_id)
        workdays.append(actual_workday)

    return workdays

async def get_user_workdays(session: AsyncSession, telegram_id: int) -> list[WorkDay] | []:
    return list(await session.scalars(select(WorkDay)
                                      .where(WorkDay.employee_id == telegram_id)
                                      .order_by(WorkDay.workday_date.desc())))
async def get_workday(session: AsyncSession, workday_id: int, *, telegram_id: int) -> WorkDay | None:
    return await _owned_workdays(session, workday_id, telegram_id)

async def create_workday(
        session: AsyncSession,
        employee_id: int,
        date: datetime,
        place: str,
        total_hours: int,
        formatted_hours: str,
        employee_profit: float | int,
        **kwargs
) -> WorkDay:
    workday = WorkDay(
        employee_id=employee_id,
        workday_date=date,
        total_hours=total_hours,
        workplace_name=place,
        hours_formatted=formatted_hours,
        employee_profit=employee_profit,
        **kwargs
    )
    session.add(workday)
    await session.flush()
    return workday

async def update_workday(
        session: AsyncSession,
        workday_id: int,
        user_id: int,
        **kwargs
) -> None | WorkDay:
    workday: WorkDay | None = await get_workday(session, workday_id, telegram_id=user_id)

    if workday is None:
        return None

    for arg, val in kwargs.items():
        setattr(workday, arg, val)

    await session.flush()
    return workday

async def delete_workday(session: AsyncSession, workday_id: int, user_id: int) -> bool:
    workday = await get_workday(session, workday_id, telegram_id=user_id)
    if workday is None:
        return False
    await session.delete(workday)
    await session.flush()
    return True
