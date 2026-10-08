from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.db.base import Base

if TYPE_CHECKING:
    from bot.db.models.location import Location
    from bot.db.models.registration import Registration


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint("location_id", "name", name="uq_room_location_name"),
        CheckConstraint("capacity > 0", name="chk_room_capacity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    location_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    location: Mapped["Location"] = relationship("Location", back_populates="rooms")
    registrations: Mapped[List["Registration"]] = relationship("Registration", back_populates="room")

    def __repr__(self) -> str:
        return f"<Room id={self.id} name={self.name} capacity={self.capacity} sort_order={self.sort_order}>"
