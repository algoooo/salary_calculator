from typing import TYPE_CHECKING

from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.types import Integer, BigInteger, String, Float
from database.models.base import Base


if TYPE_CHECKING:
    from database.models.workday import WorkDay

class User(Base):

    __tablename__ = 'user'
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[String] = mapped_column(String, nullable=True)

    salary_per_hour: Mapped[int] = mapped_column(Integer, nullable=True)
    sales_percent: Mapped[int] = mapped_column(Integer, nullable=True)

    total_unpaid: Mapped[float] = mapped_column(Float, nullable=True)

    workdays: Mapped[list["WorkDay"]] = relationship("WorkDay", back_populates="user", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return (f"{self.telegram_id}: "
                f"@{self.username}, "
                f"payment: [{self.salary_per_hour}/{self.sales_percent}%], "
                f"unpaid: [{self.total_unpaid}]")

