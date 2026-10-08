import datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.db.base import Base

if TYPE_CHECKING:
    from bot.db.models.room import Room
    from bot.db.models.session import ExamSession
    from bot.db.models.student import Student


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (
        CheckConstraint("seat_no > 0", name="chk_reg_seat_positive"),
        CheckConstraint("status IN ('active', 'cancelled')", name="chk_reg_status"),
        Index(
            "uq_student_session",
            "student_id",
            "session_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
        Index(
            "uq_seat",
            "session_id",
            "room_id",
            "seat_no",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
        Index("idx_reg_session", "session_id", "room_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exam_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id"),
        nullable=False,
    )
    seat_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    student: Mapped["Student"] = relationship("Student", back_populates="registrations")
    session: Mapped["ExamSession"] = relationship("ExamSession", back_populates="registrations")
    room: Mapped["Room"] = relationship("Room", back_populates="registrations")

    def __repr__(self) -> str:
        return (
            f"<Registration id={self.id} student_id={self.student_id} "
            f"session_id={self.session_id} room_id={self.room_id} "
            f"seat_no={self.seat_no} status={self.status}>"
        )
