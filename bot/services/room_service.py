from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.room import Room


class RoomService:
    @staticmethod
    async def create_room(
        session: AsyncSession,
        location_id: int,
        name: str,
        capacity: int,
        sort_order: int = 0,
    ) -> Room:
        """Yangi xona yaratish"""
        room = Room(
            location_id=location_id,
            name=name.strip(),
            capacity=capacity,
            sort_order=sort_order,
            is_active=True,
        )
        session.add(room)
        await session.commit()
        await session.refresh(room)
        return room

    @staticmethod
    async def get_rooms_by_location(
        session: AsyncSession,
        location_id: int,
        active_only: bool = True,
    ) -> List[Room]:
        """Manzildagi barcha xonalar (sort_order bo'yicha saralangan)"""
        query = select(Room).where(Room.location_id == location_id)
        if active_only:
            query = query.where(Room.is_active == True)
        query = query.order_by(Room.sort_order.asc(), Room.id.asc())
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_room_by_id(session: AsyncSession, room_id: int) -> Optional[Room]:
        """Xonani ID bo'yicha olish"""
        result = await session.execute(select(Room).where(Room.id == room_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_room(
        session: AsyncSession,
        room_id: int,
        name: Optional[str] = None,
        capacity: Optional[int] = None,
        sort_order: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Room]:
        """Xona ma'lumotlarini tahrirlash"""
        room = await RoomService.get_room_by_id(session, room_id)
        if not room:
            return None
        if name is not None:
            room.name = name.strip()
        if capacity is not None and capacity > 0:
            room.capacity = capacity
        if sort_order is not None:
            room.sort_order = sort_order
        if is_active is not None:
            room.is_active = is_active
        await session.commit()
        await session.refresh(room)
        return room

    @staticmethod
    async def delete_room(session: AsyncSession, room_id: int) -> bool:
        """Xonani o'chirish"""
        try:
            result = await session.execute(delete(Room).where(Room.id == room_id))
            await session.commit()
            return (result.rowcount or 0) > 0
        except IntegrityError:
            await session.rollback()
            return False

