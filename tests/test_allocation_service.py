import asyncio
import datetime
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.db.models import ExamSession
from bot.services.allocation_service import AllocationService


@pytest.mark.asyncio
async def test_room_filling_and_overflow(db_session: AsyncSession, sample_setup):
    """
    1-TEST: Xona to'lishi va keyingi xonaga avtomatik o'tish:
    101-xona (sig'imi 2):
    - 1-o'quvchi -> 101-xona, 1-stol (room_changed = False)
    - 2-o'quvchi -> 101-xona, 2-stol (room_changed = False)
    101-xona to'ldi!
    - 3-o'quvchi -> 102-xona, 1-stol (room_changed = True)
    """
    exam_session = sample_setup["session"]
    students = sample_setup["students"]

    # 1-o'quvchi
    res1 = await AllocationService.allocate_seat(db_session, students[0].id, exam_session.id)
    assert res1.success is True
    assert res1.room_name == "101-xona"
    assert res1.seat_no == 1
    assert res1.room_changed is False

    # 2-o'quvchi
    res2 = await AllocationService.allocate_seat(db_session, students[1].id, exam_session.id)
    assert res2.success is True
    assert res2.room_name == "101-xona"
    assert res2.seat_no == 2
    assert res2.room_changed is False

    # 3-o'quvchi (101-xona to'lgan, 102-xonaga o'tishi kerak)
    res3 = await AllocationService.allocate_seat(db_session, students[2].id, exam_session.id)
    assert res3.success is True
    assert res3.room_name == "102-xona"
    assert res3.seat_no == 1
    assert res3.room_changed is True  # Xona o'zgardi!


@pytest.mark.asyncio
async def test_all_rooms_full_and_alternative_suggestion(db_session: AsyncSession, sample_setup):
    """
    2-TEST: Barcha xonalar to'lishi:
    Jami 4 ta joy mavjud (2 xonada 2 tadan).
    4 ta o'quvchi joylashgach, seans status='full' bo'ladi.
    5-o'quvchi yozilmoqchi bo'lsa, xatolik beriladi va muqobil seans taklif qilinadi.
    """
    exam_session = sample_setup["session"]
    students = sample_setup["students"]
    subject = sample_setup["subject"]
    location = sample_setup["location"]

    # Muqobil seans yaratamiz (o'sha kuni soat 16:00 da)
    alt_session = ExamSession(
        subject_id=subject.id,
        location_id=location.id,
        exam_date=exam_session.exam_date,
        start_time=datetime.time(16, 0),
        status="open",
    )
    db_session.add(alt_session)
    await db_session.commit()

    # Dastlabki 4 ta o'quvchini joylashtirish
    for i in range(4):
        res = await AllocationService.allocate_seat(db_session, students[i].id, exam_session.id)
        assert res.success is True

    # Seans status='full' bo'lganini tekshirish
    await db_session.refresh(exam_session)
    assert exam_session.status == "full"

    # 5-o'quvchi to'lgan seansga urinib ko'radi
    res5 = await AllocationService.allocate_seat(db_session, students[4].id, exam_session.id)
    assert res5.success is False
    assert res5.error_code == "SESSION_FULL"
    assert res5.suggested_session is not None
    assert res5.suggested_session.id == alt_session.id
    assert res5.suggested_session.start_time == datetime.time(16, 0)


@pytest.mark.asyncio
async def test_cancellation_and_seat_reallocation(db_session: AsyncSession, sample_setup):
    """
    3-TEST: Bekor qilingandan keyin joy qayta berilishi:
    1-o'quvchi 101-xona, 1-stolga yoziladi.
    So'ng o'z ro'yxatini bekor qiladi (status='cancelled').
    2-o'quvchi yozilganda aynan o'sha bo'shagan 1-stolni oladi.
    """
    exam_session = sample_setup["session"]
    students = sample_setup["students"]

    # 1-o'quvchi joy oladi
    res1 = await AllocationService.allocate_seat(db_session, students[0].id, exam_session.id)
    assert res1.success is True
    assert res1.room_name == "101-xona"
    assert res1.seat_no == 1
    reg1_id = res1.registration.id

    # 1-o'quvchi bekor qiladi
    cancel_success = await AllocationService.cancel_registration(
        db_session, registration_id=reg1_id, student_id=students[0].id
    )
    assert cancel_success is True

    # 2-o'quvchi ro'yxatdan o'tadi — bo'shagan 1-stol unga berilishi kerak
    res2 = await AllocationService.allocate_seat(db_session, students[1].id, exam_session.id)
    assert res2.success is True
    assert res2.room_name == "101-xona"
    assert res2.seat_no == 1  # 1-stol qayta ajratildi!


@pytest.mark.asyncio
async def test_duplicate_registration_prevented(db_session: AsyncSession, sample_setup):
    """
    QO'SHIMCHA TEST: Bitta o'quvchi bir seansga ikki marta yozilolmasligi:
    """
    exam_session = sample_setup["session"]
    student = sample_setup["students"][0]

    # Birinchi marta yozilish
    res1 = await AllocationService.allocate_seat(db_session, student.id, exam_session.id)
    assert res1.success is True

    # Ikkinchi marta o'sha seansga yozilishga urinish
    res2 = await AllocationService.allocate_seat(db_session, student.id, exam_session.id)
    assert res2.success is False
    assert res2.error_code == "ALREADY_REGISTERED"


@pytest.mark.asyncio
async def test_concurrent_allocations(async_engine, sample_setup):
    """
    4-TEST: Parallel so'rovlar (asyncio.gather):
    4 ta o'quvchi bir vaqtning o'zida alohida DB sessiyalarida so'rov yuboradi.
    Natijada birorta ham stol takrorlanmasligi (uq_seat buzilmasligi) va barchasi
    to'g'ri taqsimlanishi kerak.
    """
    exam_session_id = sample_setup["session"].id
    student_ids = [s.id for s in sample_setup["students"][:4]]

    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def book_student(s_id: int):
        async with session_factory() as session:
            return await AllocationService.allocate_seat(session, student_id=s_id, session_id=exam_session_id)

    # 4 ta parallel so'rovni bir vaqtda jo'natamiz
    results = await asyncio.gather(*[book_student(s_id) for s_id in student_ids])

    # Barcha so'rovlar muvaffaqiyatli bo'lganini tekshiramiz
    successes = [r for r in results if r.success]
    assert len(successes) == 4, f"All results: {[(r.success, r.error_code, r.error_message) for r in results]}"

    # Ajratilgan (xona, stol) juftliklari takrorlanmaganligini tekshirish
    allocated_seats = [(r.room_name, r.seat_no) for r in successes]
    unique_seats = set(allocated_seats)
    assert len(unique_seats) == 4, f"Stollar takrorlandi: {allocated_seats}"
