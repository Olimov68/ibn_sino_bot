from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.config import settings
from bot.db.models.admin import Admin


class AdminService:
    @staticmethod
    async def is_admin(session: AsyncSession, telegram_id: int) -> bool:
        """Foydalanuvchi admin ekanligini tekshirish (.env yoki admins jadvali orqali)"""
        if telegram_id in settings.admin_ids_list:
            return True

        query = select(Admin).where(Admin.telegram_id == telegram_id)
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def add_admin(
        session: AsyncSession,
        telegram_id: int,
        full_name: Optional[str] = None,
    ) -> Admin:
        """Yangi admin qo'shish"""
        existing = await session.execute(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )
        admin = existing.scalar_one_or_none()
        if admin:
            if full_name:
                admin.full_name = full_name
                await session.commit()
            return admin

        new_admin = Admin(telegram_id=telegram_id, full_name=full_name)
        session.add(new_admin)
        await session.commit()
        await session.refresh(new_admin)
        return new_admin

    @staticmethod
    async def remove_admin(session: AsyncSession, telegram_id: int) -> bool:
        """Adminni o'chirish"""
        result = await session.execute(
            delete(Admin).where(Admin.telegram_id == telegram_id)
        )
        await session.commit()
        return (result.rowcount or 0) > 0

    @staticmethod
    async def get_all_admins(session: AsyncSession) -> List[Admin]:
        """Barcha adminlar ro'yxatini olish"""
        result = await session.execute(select(Admin).order_by(Admin.id))
        return list(result.scalars().all())

    @staticmethod
    async def init_default_admins(session: AsyncSession) -> None:
        """settings.admin_ids_list dagi adminlarni bazaga kiritish"""
        for admin_id in settings.admin_ids_list:
            existing = await session.execute(
                select(Admin).where(Admin.telegram_id == admin_id)
            )
            if not existing.scalar_one_or_none():
                session.add(Admin(telegram_id=admin_id, full_name="Super Admin"))
        await session.commit()

