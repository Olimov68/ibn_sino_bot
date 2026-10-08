import datetime
import os
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.base import Base
from bot.db.models import Location, Room, Subject, ExamSession, Student

TEST_DB_FILE = "test_run.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Test ma'lumotlar bazasi dvigateli"""
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass



@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Har bir test uchun toza asinxron DB sessiyasi"""
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def sample_setup(db_session: AsyncSession):
    """
    Standart test muhiti:
    1 ta manzil, 1 ta fan, 2 ta xona (har birining sig'imi 2 tadan, jami 4 ta joy),
    1 ta ochiq imtihon seansi va 5 ta o'quvchi.
    """
    # 1. Manzil
    location = Location(name="Bosh bino", address="Navoiy ko'chasi, 15-uy", is_active=True)
    db_session.add(location)
    await db_session.flush()

    # 2. Xonalar (sort_order bo'yicha)
    room1 = Room(location_id=location.id, name="101-xona", capacity=2, sort_order=1, is_active=True)
    room2 = Room(location_id=location.id, name="102-xona", capacity=2, sort_order=2, is_active=True)
    db_session.add_all([room1, room2])
    await db_session.flush()

    # 3. Fan
    subject = Subject(name="Kimyo")
    db_session.add(subject)
    await db_session.flush()

    # 4. Imtihon seansi (Ertaga 14:00 da)
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    exam_time = datetime.time(14, 0)
    session = ExamSession(
        subject_id=subject.id,
        location_id=location.id,
        exam_date=tomorrow,
        start_time=exam_time,
        status="open",
    )
    db_session.add(session)
    await db_session.flush()

    # 5. O'quvchilar
    students = []
    for i in range(1, 6):
        student = Student(
            telegram_id=1000 + i,
            full_name=f"O'quvchi {i}",
            phone=f"+99890123450{i}",
            grade=10,
        )
        students.append(student)
        db_session.add(student)

    await db_session.commit()

    return {
        "location": location,
        "rooms": [room1, room2],
        "subject": subject,
        "session": session,
        "students": students,
    }
