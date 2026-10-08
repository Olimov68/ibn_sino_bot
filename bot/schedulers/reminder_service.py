import asyncio
import datetime
from typing import Set
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.db.models.registration import Registration
from bot.db.models.session import ExamSession
from bot.db.session import async_session_maker

# Yuborilgan eslatmalarni takrorlamaslik uchun xotirada saqlash to'plami
_sent_reminders: Set[str] = set()


class ReminderService:
    @staticmethod
    async def check_and_send_reminders(bot: Bot) -> None:
        """
        Imtihonga 1 kun (24 soat) va 2 soat qolgan o'quvchilarga avtomatik eslatma yuborish
        """
        async with async_session_maker() as session:
            now = datetime.datetime.now()
            today = now.date()

            # Faqat bugun, ertaga va keyingi kundagi faol ro'yxatlarni yuklash
            max_date = today + datetime.timedelta(days=2)
            query = (
                select(Registration)
                .join(Registration.session)
                .where(
                    Registration.status == "active",
                    ExamSession.exam_date >= today,
                    ExamSession.exam_date <= max_date,
                )
                .options(
                    selectinload(Registration.student),
                    selectinload(Registration.room),
                    selectinload(Registration.session).selectinload(ExamSession.subject),
                    selectinload(Registration.session).selectinload(ExamSession.location),
                )
            )
            registrations = list((await session.execute(query)).scalars().all())

            for reg in registrations:
                if not reg.student or not reg.student.telegram_id:
                    continue

                exam_dt = datetime.datetime.combine(reg.session.exam_date, reg.session.start_time)
                diff_seconds = (exam_dt - now).total_seconds()
                diff_hours = diff_seconds / 3600.0

                # 1. Imtihondan 1 kun (23.5 - 24.5 soat) oldin
                if 23.5 <= diff_hours <= 24.5:
                    key = f"{reg.id}:1_day"
                    if key not in _sent_reminders:
                        text = (
                            f"⏰ <b>ESLATMA: IMTIHON ERTAGA!</b>\n\n"
                            f"Hurmatli <b>{reg.student.full_name}</b>, ertaga sizning mock imtihoningiz bo'lib o'tadi:\n\n"
                            f"📚 <b>Fan:</b> {reg.session.subject.name}\n"
                            f"📅 <b>Sana:</b> {reg.session.exam_date.strftime('%d.%m.%Y')}\n"
                            f"🕑 <b>Vaqt:</b> {reg.session.start_time.strftime('%H:%M')}\n"
                            f"📍 <b>Manzil:</b> {reg.session.location.name} ({reg.session.location.address})\n"
                            f"🚪 <b>Xona:</b> {reg.room.name}\n"
                            f"🪑 <b>Stol:</b> {reg.seat_no}\n\n"
                            f"<i>Iltimos, o'z vaqtida kelishingizni va o'zingiz bilan shaxsingizni tasdiqlovchi hujjat "
                            f"hamda qora/ko'k ruchka olishingizni so'raymiz! 🎯</i>"
                        )
                        await ReminderService._send_message_safe(bot, reg.student.telegram_id, text)
                        _sent_reminders.add(key)

                # 2. Imtihondan 2 soat (1.8 - 2.2 soat) oldin
                elif 1.8 <= diff_hours <= 2.2:
                    key = f"{reg.id}:2_hours"
                    if key not in _sent_reminders:
                        text = (
                            f"⏳ <b>DIQQAT: IMTIHONGA 2 SOAT QOLDI!</b>\n\n"
                            f"Hurmatli <b>{reg.student.full_name}</b>, imtihon boshlanishiga 2 soat qoldi:\n\n"
                            f"📚 <b>Fan:</b> {reg.session.subject.name}\n"
                            f"🕑 <b>Boshlanish vaqti:</b> {reg.session.start_time.strftime('%H:%M')}\n"
                            f"📍 <b>Manzil:</b> {reg.session.location.name} ({reg.session.location.address})\n"
                            f"🚪 <b>Xona:</b> {reg.room.name}\n"
                            f"🪑 <b>Stol:</b> {reg.seat_no}\n\n"
                            f"<i>Imtihon markaziga kechikmasdan yetib kelishingizni so'raymiz. "
                            f"Sizga muvaffaqiyat va yuqori natijalar tilaymiz! 🌟</i>"
                        )
                        await ReminderService._send_message_safe(bot, reg.student.telegram_id, text)
                        _sent_reminders.add(key)

    @staticmethod
    async def _send_message_safe(bot: Bot, chat_id: int, text: str) -> None:
        """Xatoliklarni ushlab xavfsiz xabar yuborish"""
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            await asyncio.sleep(0.05)
        except Exception:
            pass


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """APScheduler ni sozlash va ishga tushirish"""
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    # Har 5 daqiqada tekshiradi
    scheduler.add_job(
        ReminderService.check_and_send_reminders,
        trigger="interval",
        minutes=5,
        kwargs={"bot": bot},
        id="check_exam_reminders",
        replace_existing=True,
    )
    return scheduler
