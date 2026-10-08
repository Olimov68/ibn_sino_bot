import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db.models.location import Location
from bot.db.models.registration import Registration
from bot.db.models.room import Room
from bot.db.models.session import ExamSession
from bot.db.models.subject import Subject


class SessionService:
    @staticmethod
    async def create_session(
        session: AsyncSession,
        subject_id: int,
        location_id: int,
        exam_date: datetime.date,
        start_time: datetime.time,
        mode: str = "offline",
    ) -> ExamSession:
        """Yangi imtihon seansi yaratish"""
        new_session = ExamSession(
            subject_id=subject_id,
            location_id=location_id,
            exam_date=exam_date,
            start_time=start_time,
            mode=mode,
            status="open",
        )
        session.add(new_session)
        await session.commit()
        await session.refresh(new_session)
        return new_session

    @staticmethod
    async def get_session_by_id(
        session: AsyncSession,
        session_id: int,
    ) -> Optional[ExamSession]:
        """Seansni ID bo'yicha bog'liq modellar bilan olish"""
        query = (
            select(ExamSession)
            .where(ExamSession.id == session_id)
            .options(
                selectinload(ExamSession.subject),
                selectinload(ExamSession.location),
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def close_session(session: AsyncSession, session_id: int) -> bool:
        """Seansni yopish (status = 'closed')"""
        exam_session = await session.get(ExamSession, session_id)
        if not exam_session:
            return False
        exam_session.status = "closed"
        await session.commit()
        return True

    @staticmethod
    async def get_session_capacity_info(
        session: AsyncSession,
        session_id: int,
    ) -> Dict[str, Any]:
        """Seansning umumiy sig'imi, band va bo'sh joylari haqida ma'lumot"""
        exam_session = await session.get(ExamSession, session_id)
        if not exam_session:
            return {"total": 0, "registered": 0, "remaining": 0}

        # Manzildagi barcha faol xonalar sig'imi yig'indisi
        rooms_capacity_query = select(func.coalesce(func.sum(Room.capacity), 0)).where(
            Room.location_id == exam_session.location_id,
            Room.is_active == True,
        )
        total_capacity = (await session.execute(rooms_capacity_query)).scalar_one()

        # Faol ro'yxatdan o'tganlar soni
        reg_count_query = select(func.count(Registration.id)).where(
            Registration.session_id == session_id,
            Registration.status == "active",
        )
        registered_count = (await session.execute(reg_count_query)).scalar_one()

        remaining = max(0, total_capacity - registered_count)
        return {
            "total": total_capacity,
            "registered": registered_count,
            "remaining": remaining,
        }

    @staticmethod
    async def get_distinct_dates_for_subject(
        session: AsyncSession,
        subject_id: int,
    ) -> List[datetime.date]:
        """Fan bo'yicha ochiq bo'lgan va o'rinlari bor seanslarning betakror kelajak sanalari"""
        now = datetime.datetime.now()
        today = now.date()
        current_time = now.time()

        query = (
            select(ExamSession)
            .where(
                ExamSession.subject_id == subject_id,
                ExamSession.status == "open",
                ExamSession.exam_date >= today,
            )
            .order_by(ExamSession.exam_date.asc(), ExamSession.start_time.asc())
        )
        result = await session.execute(query)
        sessions = list(result.scalars().all())

        valid_dates: List[datetime.date] = []
        for sess in sessions:
            if sess.exam_date == today and sess.start_time <= current_time:
                continue
            cap_info = await SessionService.get_session_capacity_info(session, sess.id)
            if cap_info["remaining"] > 0:
                if sess.exam_date not in valid_dates:
                    valid_dates.append(sess.exam_date)

        return valid_dates

    @staticmethod
    async def get_sessions_for_subject_and_date(
        session: AsyncSession,
        subject_id: int,
        exam_date: datetime.date,
    ) -> List[Dict[str, Any]]:
        """Fan va sana bo'yicha seanslar ro'yxati (o'tib ketmagan va bo'sh joyi bor)"""
        now = datetime.datetime.now()
        today = now.date()
        current_time = now.time()

        query = (
            select(ExamSession)
            .where(
                ExamSession.subject_id == subject_id,
                ExamSession.exam_date == exam_date,
                ExamSession.status == "open",
            )
            .options(
                selectinload(ExamSession.subject),
                selectinload(ExamSession.location),
            )
            .order_by(ExamSession.start_time.asc())
        )
        result = await session.execute(query)
        sessions = list(result.scalars().all())

        items: List[Dict[str, Any]] = []
        for sess in sessions:
            if sess.exam_date == today and sess.start_time <= current_time:
                continue
            cap_info = await SessionService.get_session_capacity_info(session, sess.id)
            if cap_info["remaining"] > 0:
                items.append({
                    "session": sess,
                    "remaining": cap_info["remaining"],
                    "total": cap_info["total"],
                    "registered": cap_info["registered"],
                })
        return items

    @staticmethod
    async def get_all_active_sessions(
        session: AsyncSession,
        limit: int = 50,
    ) -> List[ExamSession]:
        """Admin paneli uchun barcha yaqinlashayotgan seanslar"""
        query = (
            select(ExamSession)
            .options(
                selectinload(ExamSession.subject),
                selectinload(ExamSession.location),
            )
            .order_by(ExamSession.exam_date.desc(), ExamSession.start_time.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())
