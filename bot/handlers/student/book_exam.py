import datetime
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.student_kb import (
    get_student_dates_kb,
    get_student_main_menu_kb,
    get_student_subjects_kb,
    get_student_times_kb,
)
from bot.services.allocation_service import AllocationService
from bot.services.session_service import SessionService
from bot.services.student_service import StudentService
from bot.services.subject_service import SubjectService
from bot.states.student_states import StudentBookingStates

student_booking_router = Router(name="student_booking")


@student_booking_router.message(F.text == "📝 Imtihonga yozilish")
async def start_booking_from_menu(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Imtihonga yozilishni boshlash: 1-qadam — Fanni tanlash"""
    await state.clear()
    student = await StudentService.get_student_by_telegram_id(session, message.from_user.id)
    if not student:
        await message.answer("⚠️ Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
        return

    subjects = await SubjectService.get_subjects(session)
    if not subjects:
        await message.answer("ℹ️ Hozircha rejalashtirilgan imtihon fanlari mavjud emas.")
        return

    await state.set_state(StudentBookingStates.waiting_subject)
    await message.answer(
        "📝 <b>Imtihonga yozilish</b>\n\n1️⃣ Qaysi fandan mock imtihon topshirmoqchisiz? Fanni tanlang:",
        reply_markup=get_student_subjects_kb(subjects),
        parse_mode="HTML",
    )


@student_booking_router.callback_query(F.data == "stu_book_start")
async def back_to_subjects(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Fanlar ro'yxatiga qaytish"""
    await state.clear()
    await callback.answer()
    subjects = await SubjectService.get_subjects(session)
    if callback.message:
        await callback.message.edit_text(
            "📝 <b>Imtihonga yozilish</b>\n\n1️⃣ Qaysi fandan mock imtihon topshirmoqchisiz? Fanni tanlang:",
            reply_markup=get_student_subjects_kb(subjects),
            parse_mode="HTML",
        )


@student_booking_router.callback_query(F.data.startswith("stu_sub:"))
async def process_subject_select(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Fanni tanlash: 2-qadam — Sanani tanlash"""
    await callback.answer()
    sub_id = int(callback.data.split(":")[1])
    subject = await SubjectService.get_subject_by_id(session, sub_id)
    if not subject:
        if callback.message:
            await callback.message.edit_text("⚠️ Fan topilmadi.")
        return

    await state.update_data(subject_id=sub_id, subject_name=subject.name)

    # Fan bo'yicha ochiq sanalarni olish
    dates = await SessionService.get_distinct_dates_for_subject(session, sub_id)
    if not dates:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Boshqa fan tanlash", callback_data="stu_book_start")]]
        )
        if callback.message:
            await callback.message.edit_text(
                f"ℹ️ <b>{subject.name}</b> fani bo'yicha hozircha bo'sh o'rinli imtihon seanslari mavjud emas.",
                reply_markup=kb,
                parse_mode="HTML",
            )
        return

    await state.set_state(StudentBookingStates.waiting_date)
    if callback.message:
        await callback.message.edit_text(
            f"📚 Tanlangan fan: <b>{subject.name}</b>\n\n2️⃣ Imtihon kunini (sanasini) tanlang:",
            reply_markup=get_student_dates_kb(dates),
            parse_mode="HTML",
        )


@student_booking_router.callback_query(F.data.startswith("stu_date:"))
async def process_date_select(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Sanani tanlash: 3-qadam — Vaqtni tanlash"""
    await callback.answer()
    date_str = callback.data.split(":")[1]
    exam_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()

    data = await state.get_data()
    sub_id = data.get("subject_id")
    sub_name = data.get("subject_name")

    if not sub_id:
        if callback.message:
            await callback.message.edit_text(
                "⚠️ Sessiya muddati tugagan. Iltimos, fanni boshidan tanlang:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="📝 Imtihonga yozilish", callback_data="stu_book_start")]]
                ),
                parse_mode="HTML",
            )
        return

    await state.update_data(exam_date=date_str)

    # Fan va sana bo'yicha seanslarni olish
    session_items = await SessionService.get_sessions_for_subject_and_date(session, sub_id, exam_date)
    if not session_items:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Boshqa sana tanlash", callback_data=f"stu_sub:{sub_id}")]]
        )
        if callback.message:
            await callback.message.edit_text(
                f"⚠️ <b>{date_str}</b> sanasida barcha joylar to'lgan yoki seanslar mavjud emas.",
                reply_markup=kb,
                parse_mode="HTML",
            )
        return

    await state.set_state(StudentBookingStates.waiting_time)
    if callback.message:
        await callback.message.edit_text(
            f"📚 Fan: <b>{sub_name}</b>\n📅 Sana: <b>{date_str}</b>\n\n"
            f"3️⃣ O'zingizga qulay bo'lgan vaqtni va manzilni tanlang:\n<i>(Har bir vaqt yonida qolgan bo'sh joylar soni ko'rsatilgan)</i>",
            reply_markup=get_student_times_kb(session_items),
            parse_mode="HTML",
        )


@student_booking_router.callback_query(F.data == "stu_back_dates")
async def back_to_dates(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Sanalar ro'yxatiga qaytish"""
    await callback.answer()
    data = await state.get_data()
    sub_id = data.get("subject_id")
    sub_name = data.get("subject_name")

    if not sub_id:
        if callback.message:
            await callback.message.edit_text(
                "⚠️ Iltimos, fanni qaytadan tanlang:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="📝 Imtihonga yozilish", callback_data="stu_book_start")]]
                ),
                parse_mode="HTML",
            )
        return

    dates = await SessionService.get_distinct_dates_for_subject(session, sub_id)
    if callback.message:
        await callback.message.edit_text(
            f"📚 Fan: <b>{sub_name}</b>\n\n2️⃣ Imtihon kunini tanlang:",
            reply_markup=get_student_dates_kb(dates),
            parse_mode="HTML",
        )


@student_booking_router.callback_query(F.data.startswith("stu_sess:"))
async def process_session_booking(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Joy ajratish va tasdiqlash"""
    await callback.answer("Joy band qilinmoqda...", show_alert=False)
    sess_id = int(callback.data.split(":")[1])

    student = await StudentService.get_student_by_telegram_id(session, callback.from_user.id)
    if not student:
        if callback.message:
            await callback.message.edit_text("⚠️ O'quvchi profili topilmadi.")
        return

    # Joylashtirish xizmatini chaqirish (Concurrency protected, transaction-bound)
    result = await AllocationService.allocate_seat(session, student_id=student.id, session_id=sess_id)
    await state.clear()

    if result.success and result.registration:
        reg = result.registration
        date_formatted = reg.session.exam_date.strftime("%d.%m.%Y")
        time_formatted = reg.session.start_time.strftime("%H:%M")

        room_changed_note = ""
        if result.room_changed:
            room_changed_note = (
                f"\n\n🔔 <b>DIQQAT:</b> Asosiy xona to'lganligi sababli siz keyingi bo'sh xonaga joylashtirildingiz! "
                f"Iltimos, <b>{result.room_name}</b> xonasiga boring."
            )

        confirm_text = (
            f"✅ <b>Ro'yxatdan o'tdingiz!</b>\n\n"
            f"📚 <b>Fan:</b> {reg.session.subject.name}\n"
            f"📍 <b>Manzil:</b> {reg.session.location.name} ({reg.session.location.address})\n"
            f"🚪 <b>Xona:</b> {reg.room.name}\n"
            f"🪑 <b>Stol:</b> {reg.seat_no}\n"
            f"📅 <b>Sana:</b> {date_formatted}\n"
            f"🕑 <b>Vaqt:</b> {time_formatted}"
            f"{room_changed_note}\n\n"
            f"<i>Imtihonga o'z vaqtida shaxsingizni tasdiqlovchi hujjat va ruchka bilan kelishingizni so'raymiz. Omad tilaymiz! 🌟</i>"
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋 Mening ro'yxatlarim", callback_data="stu_my_exams_cb")],
                [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home")],
            ]
        )

        if callback.message:
            await callback.message.edit_text(confirm_text, reply_markup=kb, parse_mode="HTML")

    elif result.error_code == "ALREADY_REGISTERED":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋 Mening ro'yxatlarim", callback_data="stu_my_exams_cb")],
                [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home")],
            ]
        )
        if callback.message:
            await callback.message.edit_text(
                "⚠️ <b>Siz ushbu imtihon seansiga allaqachon ro'yxatdan o'tgansiz!</b>\n\n"
                "O'z joyingiz va stolingizni «Mening ro'yxatlarim» bo'limida ko'rishingiz mumkin.",
                reply_markup=kb,
                parse_mode="HTML",
            )

    elif result.error_code == "SESSION_FULL":
        alt_kb: List[List[InlineKeyboardButton]] = []
        alt_msg = "❌ <b>Afsuski, ushbu seansdagi barcha o'rinlar to'ldi!</b>"

        if result.suggested_session:
            alt = result.suggested_session
            alt_date = alt.exam_date.strftime("%d.%m.%Y")
            alt_time = alt.start_time.strftime("%H:%M")
            alt_msg += (
                f"\n\n💡 <b>Sizga tavsiya qilingan keyingi bo'sh seans:</b>\n"
                f"📚 Fan: {alt.subject.name}\n"
                f"📅 Sana: {alt_date}\n"
                f"🕑 Vaqt: {alt_time}\n"
                f"📍 Bino: {alt.location.name}"
            )
            alt_kb.append([
                InlineKeyboardButton(
                    text=f"👉 Ushbu vaqtga yozilish ({alt_time})",
                    callback_data=f"stu_sess:{alt.id}",
                )
            ])

        alt_kb.append([InlineKeyboardButton(text="⬅️ Boshqa vaqt tanlash", callback_data="stu_book_start")])
        alt_kb.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home")])

        if callback.message:
            await callback.message.edit_text(
                alt_msg,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=alt_kb),
                parse_mode="HTML",
            )

    else:
        if callback.message:
            await callback.message.edit_text(
                f"⚠️ {result.error_message or 'Kutilmagan xatolik yuz berdi.'}",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home")]]
                ),
                parse_mode="HTML",
            )
