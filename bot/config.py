from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    DATABASE_URL: str = "postgresql+asyncpg://ibnsino:ibnsino_password@localhost:5432/ibnsino_db"
    ADMIN_IDS: str = ""

    @property
    def admin_ids_list(self) -> List[int]:
        """ADMIN_IDS satrini butun sonlar (int) ro'yxatiga aylantirish"""
        if not self.ADMIN_IDS:
            return []
        result: List[int] = []
        for item in self.ADMIN_IDS.split(","):
            cleaned = item.strip()
            if cleaned.isdigit() or (cleaned.startswith("-") and cleaned[1:].isdigit()):
                result.append(int(cleaned))
        return result

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
