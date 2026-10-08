from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.db.base import Base

if TYPE_CHECKING:
    from bot.db.models.room import Room
    from bot.db.models.session import ExamSession


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rooms: Mapped[List["Room"]] = relationship(
        "Room",
        back_populates="location",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[List["ExamSession"]] = relationship(
        "ExamSession",
        back_populates="location",
    )

    def __repr__(self) -> str:
        return f"<Location id={self.id} name={self.name} is_active={self.is_active}>"
