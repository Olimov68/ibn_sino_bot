from typing import Optional
from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column
from bot.db.base import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Admin id={self.id} telegram_id={self.telegram_id} full_name={self.full_name}>"
