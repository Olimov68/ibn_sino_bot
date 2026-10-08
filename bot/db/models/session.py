import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.db.base import Base

if TYPE_CHECKING:
    from bot.db.models.location import Location
    from bot.db.models.registration import Registration
    from bot.db.models.subject import Subject


class ExamSession(Base):
    __tablename__ = "exam_sessions"
    __table_args__ = (
        UniqueConstraint(
            "subject_id",
            "location_id",
            "exam_date",
            "start_time",
            name="uq_session_subject_location_datetime",
        ),
        CheckConstraint("mode IN ('offline', 'online')", name="chk_session_mode"),
        CheckConstraint("status IN ('open', 'full', 'closed')", name="chk_session_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey("subjects.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    exam_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    mode: Mapped[str] = mapped_column(Text, default="offline", nullable=False)
    status: Mapped[str] = mapped_column(Text, default="open", nullable=False)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="sessions")
    location: Mapped["Location"] = relationship("Location", back_populates="sessions")
    registrations: Mapped[List["Registration"]] = relationship(
        "Registration",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ExamSession id={self.id} subject_id={self.subject_id} "
            f"date={self.exam_date} time={self.start_time} status={self.status}>"
        )
