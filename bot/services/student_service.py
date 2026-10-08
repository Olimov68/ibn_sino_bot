from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models.student import Student


class StudentService:
    @staticmethod
    async def get_student_by_telegram_id(
        session: AsyncSession,
        telegram_id: int,
    ) -> Optional[Student]:
        """Telegram ID bo'yicha o'quvchini topish"""
        query = select(Student).where(Student.telegram_id == telegram_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_student(
        session: AsyncSession,
        telegram_id: int,
        full_name: str,
        phone: Optional[str] = None,
        grade: Optional[int] = None,
    ) -> Student:
        """O'quvchini olish yoki yangisini yaratish"""
        student = await StudentService.get_student_by_telegram_id(session, telegram_id)
        if student:
            changed = False
            if full_name and student.full_name != full_name:
                student.full_name = full_name
                changed = True
            if phone and student.phone != phone:
                student.phone = phone
                changed = True
            if grade is not None and student.grade != grade:
                student.grade = grade
                changed = True
            if changed:
                await session.commit()
                await session.refresh(student)
            return student

        # Telefon raqami bo'yicha mavjud o'quvchini tekshirish (unikal cheklov buzilmasligi uchun)
        if phone:
            phone_query = select(Student).where(Student.phone == phone.strip())
            student_by_phone = (await session.execute(phone_query)).scalar_one_or_none()
            if student_by_phone:
                student_by_phone.telegram_id = telegram_id
                student_by_phone.full_name = full_name.strip()
                if grade is not None:
                    student_by_phone.grade = grade
                await session.commit()
                await session.refresh(student_by_phone)
                return student_by_phone

        new_student = Student(
            telegram_id=telegram_id,
            full_name=full_name.strip(),
            phone=phone.strip() if phone else None,
            grade=grade,
        )
        session.add(new_student)
        await session.commit()
        await session.refresh(new_student)
        return new_student

    @staticmethod
    async def update_student(
        session: AsyncSession,
        telegram_id: int,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        grade: Optional[int] = None,
    ) -> Optional[Student]:
        """O'quvchi ma'lumotlarini yangilash"""
        student = await StudentService.get_student_by_telegram_id(session, telegram_id)
        if not student:
            return None

        if full_name is not None:
            student.full_name = full_name.strip()
        if phone is not None:
            cleaned_phone = phone.strip()
            # Boshqa o'quvchida bu raqam yo'qligini tekshirish
            phone_check = select(Student).where(Student.phone == cleaned_phone, Student.id != student.id)
            conflict = (await session.execute(phone_check)).scalar_one_or_none()
            if not conflict:
                student.phone = cleaned_phone
        if grade is not None:
            student.grade = grade

        await session.commit()
        await session.refresh(student)
        return student
