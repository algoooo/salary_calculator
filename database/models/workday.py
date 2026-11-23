from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.types import Integer, BigInteger, String, DateTime, Float
from sqlalchemy.types import Enum as SQLEnum
from database.models.base import Base
from enum import Enum

if TYPE_CHECKING:
    from database.models.user import User

class WorkdayPaidStatus(str, Enum):
    UNPAID = "Unpaid"
    PAID = "Paid"


class WorkDay(Base):
    __tablename__ = 'workday'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    employee_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.telegram_id"),
        primary_key=False)
    workday_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    workplace_name: Mapped[str] = mapped_column(String, nullable=False)

    total_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    hours_formatted: Mapped[str] = mapped_column(String, nullable=False)


    total_profit: Mapped[float] = mapped_column(Float, default=0.0)
    by_card: Mapped[float] = mapped_column(Float, default=0.0)
    by_cash: Mapped[float] = mapped_column(Float, default=0.0)
    by_transfer: Mapped[float] = mapped_column(Float, default=0.0)
    shortage: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)

    employee_profit: Mapped[float] = mapped_column(Float, nullable=False)
    pay_status: Mapped[WorkdayPaidStatus] = mapped_column(
        SQLEnum(WorkdayPaidStatus, name="workday_status"),
        nullable=False,
        default=WorkdayPaidStatus.UNPAID)

    user: Mapped["User"] = relationship(back_populates='workdays')

    def __str__(self) -> str:
        return f"{self.id} at {self.workday_date}: [{self.workplace_name}]"
