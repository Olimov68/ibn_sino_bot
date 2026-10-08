from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db.models.location import Location
from bot.db.models.registration import Registration
from bot.db.models.room import Room
from bot.db.models.session import ExamSession


@dataclass
class RoomReportItem:
    room_id: int
    room_name: str
    capacity: int
    registered: int
    free: int
    fill_percent: float


@dataclass
class SessionReport:
    session_id: int
    subject_name: str
    location_name: str
    location_address: str
    exam_date: str
    start_time: str
    status: str
    total_capacity: int
    total_registered: int
    total_free: int
    rooms: List[RoomReportItem]


class ReportService:
    @staticmethod
    async def get_session_report(
        session: AsyncSession,
        session_id: int,
    ) -> Optional[SessionReport]:
        """Seans bo'yicha to'liq statistik hisobot: xonalar to'lishi, bo'sh joylar"""
        query = (
            select(ExamSession)
            .where(ExamSession.id == session_id)
            .options(
                selectinload(ExamSession.subject),
                selectinload(ExamSession.location),
            )
        )
        exam_session = (await session.execute(query)).scalar_one_or_none()
        if not exam_session:
            return None

        # Manzildagi xonalar
        rooms_query = (
            select(Room)
            .where(
                Room.location_id == exam_session.location_id,
                Room.is_active == True,
            )
            .order_by(Room.sort_order.asc(), Room.id.asc())
        )
        rooms = list((await session.execute(rooms_query)).scalars().all())

        room_items: List[RoomReportItem] = []
        total_capacity = 0
        total_registered = 0

        for room in rooms:
            # Xonada ro'yxatdan o'tganlar soni
            count_query = select(func.count(Registration.id)).where(
                Registration.session_id == session_id,
                Registration.room_id == room.id,
                Registration.status == "active",
            )
            reg_count = (await session.execute(count_query)).scalar_one()

            free = max(0, room.capacity - reg_count)
            percent = (reg_count / room.capacity * 100) if room.capacity > 0 else 0.0

            room_items.append(
                RoomReportItem(
                    room_id=room.id,
                    room_name=room.name,
                    capacity=room.capacity,
                    registered=reg_count,
                    free=free,
                    fill_percent=round(percent, 1),
                )
            )
            total_capacity += room.capacity
            total_registered += reg_count

        total_free = max(0, total_capacity - total_registered)

        return SessionReport(
            session_id=exam_session.id,
            subject_name=exam_session.subject.name,
            location_name=exam_session.location.name,
            location_address=exam_session.location.address,
            exam_date=exam_session.exam_date.strftime("%d.%m.%Y"),
            start_time=exam_session.start_time.strftime("%H:%M"),
            status=exam_session.status,
            total_capacity=total_capacity,
            total_registered=total_registered,
            total_free=total_free,
            rooms=room_items,
        )
