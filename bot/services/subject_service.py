from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models.subject import Subject


class SubjectService:
    @staticmethod
    async def create_subject(session: AsyncSession, name: str) -> Subject:
        """Yangi fan yaratish"""
        subject = Subject(name=name.strip())
        session.add(subject)
        await session.commit()
        await session.refresh(subject)
        return subject

    @staticmethod
    async def get_subjects(session: AsyncSession) -> List[Subject]:
        """Barcha fanlar ro'yxati"""
        result = await session.execute(select(Subject).order_by(Subject.name))
        return list(result.scalars().all())

    @staticmethod
    async def get_subject_by_id(session: AsyncSession, subject_id: int) -> Optional[Subject]:
        """Fanni ID bo'yicha olish"""
        result = await session.execute(select(Subject).where(Subject.id == subject_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_subject(session: AsyncSession, subject_id: int) -> bool:
        """Fanni o'chirish"""
        try:
            result = await session.execute(delete(Subject).where(Subject.id == subject_id))
            await session.commit()
            return (result.rowcount or 0) > 0
        except IntegrityError:
            await session.rollback()
            return False

