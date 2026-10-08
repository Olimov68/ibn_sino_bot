import asyncio
import datetime
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy import func, select

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db.models.location import Location
from bot.db.models.registration import Registration
from bot.db.models.room import Room
from bot.db.models.session import ExamSession
from bot.db.models.student import Student
from bot.db.models.subject import Subject


@dataclass
class AllocationResult:
    success: bool
    registration: Optional[Registration] = None
    room_changed: bool = False
    room_name: Optional[str] = None
    seat_no: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    suggested_session: Optional[ExamSession] = None


class AllocationService:
    @staticmethod
    async def allocate_seat(
        session: AsyncSession,
        student_id: int,
        session_id: int,
    ) -> AllocationResult:
        """
        O'quvchini seansga joylashtirish algoritmi:
        1. O'quvchi bu seansga oldin yozilmaganligini tekshiradi.
        2. Xonalarni sort_order bo'yicha to'ldiradi (stol 1 dan boshlab).
        3. Birinchi xona to'lsa, keyingisiga o'tadi va room_changed=True qaytaradi.
        4. Barcha xonalar to'lsa, seans status='full' qilinadi va muqobil seans taklif qilinadi.
        5. Parallel so'rovlarda uq_seat to'qnashuvi yuz bersa, 3 marta qayta urinadi.
        """
        # 1. Oldindan faol ro'yxatdan o'tganligini tekshirish
        existing_reg_query = select(Registration).where(
            Registration.student_id == student_id,
            Registration.session_id == session_id,
            Registration.status == "active",
        )
        existing_reg = (await session.execute(existing_reg_query)).scalar_one_or_none()
        if existing_reg:
            return AllocationResult(
                success=False,
                error_code="ALREADY_REGISTERED",
                error_message="Siz ushbu imtihon seansiga allaqachon ro'yxatdan o'tgansiz!",
            )

        # 2. Qayta urinish sikli (Retry loop - 5 martagacha)
        import random
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                # Seansni olish
                exam_session = await session.get(ExamSession, session_id)
                if not exam_session:
                    return AllocationResult(
                        success=False,
                        error_code="SESSION_NOT_FOUND",
                        error_message="Imtihon seansi topilmadi!",
                    )

                if exam_session.status != "open":
                    # Seans yopiq yoki to'lgan bo'lsa muqobil vaqt izlash
                    suggested = await AllocationService._find_alternative_session(
                        session,
                        exam_session.subject_id,
                        exam_session.exam_date,
                        exam_session.start_time,
                    )
                    return AllocationResult(
                        success=False,
                        error_code="SESSION_FULL",
                        error_message="Ushbu seansda bo'sh joy qolmagan!",
                        suggested_session=suggested,
                    )

                # Manzildagi barcha faol xonalar (sort_order bo'yicha tartiblangan)
                rooms_query = (
                    select(Room)
                    .where(
                        Room.location_id == exam_session.location_id,
                        Room.is_active == True,
                    )
                    .order_by(Room.sort_order.asc(), Room.id.asc())
                )
                rooms = list((await session.execute(rooms_query)).scalars().all())

                if not rooms:
                    return AllocationResult(
                        success=False,
                        error_code="NO_ROOMS",
                        error_message="Ushbu manzilda faol xonalar topilmadi!",
                    )

                first_room = rooms[0]
                allocated_room: Optional[Room] = None
                allocated_seat: Optional[int] = None

                # Xonalarni ketma-ket to'ldirish
                for room in rooms:
                    # Ushbu xonada band bo'lgan stollar
                    taken_seats_query = select(Registration.seat_no).where(
                        Registration.session_id == session_id,
                        Registration.room_id == room.id,
                        Registration.status == "active",
                    )
                    taken_seats = set((await session.execute(taken_seats_query)).scalars().all())

                    if len(taken_seats) < room.capacity:
                        # Bo'sh stolni 1 dan boshlab qidirish
                        for seat in range(1, room.capacity + 1):
                            if seat not in taken_seats:
                                allocated_room = room
                                allocated_seat = seat
                                break
                    if allocated_seat is not None:
                        break

                if allocated_room is None or allocated_seat is None:
                    # Barcha xonalar to'ldi!
                    exam_session.status = "full"
                    await session.commit()

                    suggested = await AllocationService._find_alternative_session(
                        session,
                        exam_session.subject_id,
                        exam_session.exam_date,
                        exam_session.start_time,
                    )
                    return AllocationResult(
                        success=False,
                        error_code="SESSION_FULL",
                        error_message="Ushbu seansdagi barcha xonalar to'ldi!",
                        suggested_session=suggested,
                    )

                # Joy ajratish (DB tranzaksiyasi ichida)
                room_changed = (allocated_room.id != first_room.id)
                new_reg = Registration(
                    student_id=student_id,
                    session_id=session_id,
                    room_id=allocated_room.id,
                    seat_no=allocated_seat,
                    status="active",
                )
                session.add(new_reg)
                await session.flush()

                # Barcha xonalar to'lgan-to'lmaganligini hisoblab seans holatini tekshirish
                total_cap_query = select(func.coalesce(func.sum(Room.capacity), 0)).where(
                    Room.location_id == exam_session.location_id,
                    Room.is_active == True,
                )
                total_cap = (await session.execute(total_cap_query)).scalar_one()

                total_reg_query = select(func.count(Registration.id)).where(
                    Registration.session_id == session_id,
                    Registration.status == "active",
                )
                total_reg = (await session.execute(total_reg_query)).scalar_one()

                if total_reg >= total_cap:
                    exam_session.status = "full"

                new_reg_id = new_reg.id
                await session.commit()

                # Bog'liq modellarni yuklash
                full_reg_query = (
                    select(Registration)
                    .where(Registration.id == new_reg_id)
                    .options(
                        selectinload(Registration.room),
                        selectinload(Registration.session).selectinload(ExamSession.subject),
                        selectinload(Registration.session).selectinload(ExamSession.location),
                    )
                )
                full_reg = (await session.execute(full_reg_query)).scalar_one_or_none()
                if not full_reg:
                    new_reg.room = allocated_room
                    new_reg.session = exam_session
                    full_reg = new_reg

                return AllocationResult(
                    success=True,
                    registration=full_reg,
                    room_changed=room_changed,
                    room_name=allocated_room.name,
                    seat_no=allocated_seat,
                )

            except IntegrityError as exc:
                await session.rollback()
                first_line = str(exc).split("\n")[0].lower()

                # 1. O'quvchi qayta yozilishi xatosi
                if "uq_student_session" in first_line or "student_id" in first_line:
                    return AllocationResult(
                        success=False,
                        error_code="ALREADY_REGISTERED",
                        error_message="Siz ushbu imtihon seansiga allaqachon ro'yxatdan o'tgansiz!",
                    )

                # 2. Stol to'qnashuvi (uq_seat) xatosi
                if "uq_seat" in first_line or "seat_no" in first_line or "room_id" in first_line or "unique constraint" in first_line:
                    if attempt < max_attempts - 1:
                        # Parallel so'rov natijasida stol boshqa kishiga berildi, qayta urinamiz
                        await asyncio.sleep(0.04 * (attempt + 1) + random.uniform(0.02, 0.05))
                        continue

                # Agar urinishlar tugagan bo'lsa yoki boshqa to'qnashuv bo'lsa
                if attempt == max_attempts - 1:
                    return AllocationResult(
                        success=False,
                        error_code="CONCURRENCY_ERROR",
                        error_message="Tizim bandligi sababli qayta urinib ko'ring.",
                    )
                raise exc

        return AllocationResult(
            success=False,
            error_code="UNKNOWN_ERROR",
            error_message="Joy ajratishda xatolik yuz berdi.",
        )

    @staticmethod
    async def cancel_registration(
        session: AsyncSession,
        registration_id: int,
        student_id: int,
    ) -> bool:
        """Imtihonga yozilishni bekor qilish (status='cancelled', o'rin bo'shatiladi)"""
        reg_query = select(Registration).where(
            Registration.id == registration_id,
            Registration.student_id == student_id,
            Registration.status == "active",
        )
        reg = (await session.execute(reg_query)).scalar_one_or_none()
        if not reg:
            return False

        # O'tib ketgan imtihonni bekor qilishga ruxsat bermaslik
        exam_session = await session.get(ExamSession, reg.session_id)
        if exam_session:
            now = datetime.datetime.now()
            exam_dt = datetime.datetime.combine(exam_session.exam_date, exam_session.start_time)
            if exam_dt <= now:
                return False

            if exam_session.status == "full":
                exam_session.status = "open"

        reg.status = "cancelled"
        await session.commit()
        return True

    @staticmethod
    async def get_student_active_registrations(
        session: AsyncSession,
        student_id: int,
    ) -> List[Registration]:
        """O'quvchining faol ro'yxatdan o'tgan imtihonlari"""
        query = (
            select(Registration)
            .where(
                Registration.student_id == student_id,
                Registration.status == "active",
            )
            .options(
                selectinload(Registration.room),
                selectinload(Registration.session).selectinload(ExamSession.subject),
                selectinload(Registration.session).selectinload(ExamSession.location),
            )
            .order_by(Registration.created_at.desc())
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def _find_alternative_session(
        session: AsyncSession,
        subject_id: int,
        current_date: datetime.date,
        current_time: datetime.time,
    ) -> Optional[ExamSession]:
        """
        Shu kun va fan uchun keyingi bo'sh vaqtni taklif qilish (masalan 09:00 to'lsa 14:00),
        bo'lmasa keyingi sanani topish.
        """
        # 1. Shu kungi keyingi vaqtlarni qidirish
        same_day_query = (
            select(ExamSession)
            .where(
                ExamSession.subject_id == subject_id,
                ExamSession.exam_date == current_date,
                ExamSession.start_time > current_time,
                ExamSession.status == "open",
            )
            .options(
                selectinload(ExamSession.subject),
                selectinload(ExamSession.location),
            )
            .order_by(ExamSession.start_time.asc())
        )
        same_day_candidates = list((await session.execute(same_day_query)).scalars().all())
        for cand in same_day_candidates:
            cap = await AllocationService._has_available_seat(session, cand.id, cand.location_id)
            if cap:
                return cand

        # 2. Keyingi sanalardan birinchi bo'sh seansni qidirish
        next_days_query = (
            select(ExamSession)
            .where(
                ExamSession.subject_id == subject_id,
                ExamSession.exam_date > current_date,
                ExamSession.status == "open",
            )
            .options(
                selectinload(ExamSession.subject),
                selectinload(ExamSession.location),
            )
            .order_by(ExamSession.exam_date.asc(), ExamSession.start_time.asc())
        )
        next_day_candidates = list((await session.execute(next_days_query)).scalars().all())
        for cand in next_day_candidates:
            cap = await AllocationService._has_available_seat(session, cand.id, cand.location_id)
            if cap:
                return cand

        return None

    @staticmethod
    async def _has_available_seat(
        session: AsyncSession,
        session_id: int,
        location_id: int,
    ) -> bool:
        """Seansda kamida bitta bo'sh joy borligini aniqlash"""
        total_cap_query = select(func.coalesce(func.sum(Room.capacity), 0)).where(
            Room.location_id == location_id,
            Room.is_active == True,
        )
        total_cap = (await session.execute(total_cap_query)).scalar_one()

        total_reg_query = select(func.count(Registration.id)).where(
            Registration.session_id == session_id,
            Registration.status == "active",
        )
        total_reg = (await session.execute(total_reg_query)).scalar_one()
        return (total_cap - total_reg) > 0
