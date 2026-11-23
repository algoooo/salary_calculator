from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, WorkDay, WorkdayPaidStatus
from database.crud.workdays import get_workdays_by_date

async def create_user(
        session: AsyncSession,
        telegram_id: int,
        username: str,
        per_hour: int,
        percent: int = 0
) -> User:

    user = User(
        telegram_id=telegram_id,
        username=username,
        salary_per_hour=per_hour,
        sales_percent=percent
    )

    session.add(user)

    return user

async def update_user(
        session: AsyncSession,
        telegram_id: int,
        **kwargs
) -> User | None:

    user = await get_user(session, telegram_id)

    if user is None:
        return None

    for attr, value in kwargs.items():
        setattr(user, attr, value)

    await session.flush()
    return user

async def get_user(session: AsyncSession, telegram_id: int) -> User | None:

    return await session.get(User, telegram_id) # type: ignore

async def delete_user(session: AsyncSession, telegram_id: int) -> bool:

    user = await session.get(User, telegram_id)

    if user is None:
        return False

    await session.delete(user)
    await session.flush()

    return True

async def pay_employee(
        session: AsyncSession,
        user_id: int,
        days: list[datetime]
) -> list[WorkDay] | None:

    res: list[WorkDay] | None = await get_workdays_by_date(session, user_id, days)

    if res is None:
        return None

    for workday in res:
        workday.pay_status = WorkdayPaidStatus.PAID
        await session.flush()

    return res

