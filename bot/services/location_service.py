from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from bot.db.models.location import Location


class LocationService:
    @staticmethod
    async def create_location(session: AsyncSession, name: str, address: str) -> Location:
        """Yangi manzil yaratish"""
        loc = Location(name=name.strip(), address=address.strip())
        session.add(loc)
        await session.commit()
        await session.refresh(loc)
        return loc

    @staticmethod
    async def get_locations(session: AsyncSession, active_only: bool = True) -> List[Location]:
        """Barcha manzillar ro'yxati"""
        query = select(Location)
        if active_only:
            query = query.where(Location.is_active == True)
        query = query.order_by(Location.id)
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_location_by_id(session: AsyncSession, location_id: int) -> Optional[Location]:
        """Manzilni ID bo'yicha olish (xonalari bilan birga)"""
        query = (
            select(Location)
            .where(Location.id == location_id)
            .options(selectinload(Location.rooms))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_location(session: AsyncSession, location_id: int) -> bool:
        """Manzilni o'chirish"""
        try:
            result = await session.execute(delete(Location).where(Location.id == location_id))
            await session.commit()
            return (result.rowcount or 0) > 0
        except IntegrityError:
            await session.rollback()
            return False

