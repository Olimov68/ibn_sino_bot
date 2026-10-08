import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.db.base import Base

if TYPE_CHECKING:
    from bot.db.models.registration import Registration


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
    grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    registrations: Mapped[List["Registration"]] = relationship(
        "Registration",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Student id={self.id} full_name={self.full_name} phone={self.phone} grade={self.grade}>"
