from typing import List, TYPE_CHECKING
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.db.base import Base

if TYPE_CHECKING:
    from bot.db.models.session import ExamSession


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    sessions: Mapped[List["ExamSession"]] = relationship("ExamSession", back_populates="subject")

    def __repr__(self) -> str:
        return f"<Subject id={self.id} name={self.name}>"
