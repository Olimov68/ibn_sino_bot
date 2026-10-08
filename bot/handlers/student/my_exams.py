from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.student_kb import get_my_registrations_kb
from bot.services.allocation_service import AllocationService
from bot.services.student_service import StudentService

my_exams_router = Router(name="student_my_exams")


@my_exams_router.message(F.text == "📋 Mening ro'yxatlarim")
async def show_my_exams_menu(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """O'quvchining faol imtihonlari ro'yxati"""
    await state.clear()
    student = await StudentService.get_student_by_telegram_id(session, message.from_user.id)
    if not student:
        await message.answer("⚠️ Iltimos, avval /start orqali ro'yxatdan o'ting.")
        return

    registrations = await AllocationService.get_student_active_registrations(session, student.id)
    if not registrations:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📝 Imtihonga yozilish", callback_data="stu_book_start")],
                [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home")],
            ]
        )
        await message.answer(
            "📋 <b>Sizda hozircha faol imtihon ro'yxatlari mavjud emas.</b>\n\nImtihonga yozilish uchun quyidagi tugmani bosing:",
            reply_markup=kb,
            parse_mode="HTML",
        )
        return

    text = "📋 <b>Siz ro'yxatdan o'tgan imtihonlar:</b>\n\n"
    for idx, reg in enumerate(registrations, 1):
        d_str = reg.session.exam_date.strftime("%d.%m.%Y")
        t_str = reg.session.start_time.strftime("%H:%M")
        text += (
            f"<b>{idx}. 📚 Fan: {reg.session.subject.name}</b>\n"
            f"   📅 Sana: {d_str} | 🕑 Vaqt: {t_str}\n"
            f"   📍 Manzil: {reg.session.location.name}\n"
            f"   🚪 Xona: <b>{reg.room.name}</b> | 🪑 Stol: <b>{reg.seat_no}</b>\n\n"
        )

    text += "<i>Agar birorta imtihonga bora olmasangiz, boshqalarga imkon berish uchun uni bekor qilishingiz mumkin:</i>"
    await message.answer(text, reply_markup=get_my_registrations_kb(registrations), parse_mode="HTML")


@my_exams_router.callback_query(F.data == "stu_my_exams_cb")
async def show_my_exams_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Callback orqali ro'yxatlarni yangilash"""
    await state.clear()
    await callback.answer()
    student = await StudentService.get_student_by_telegram_id(session, callback.from_user.id)
    if not student:
        return

    registrations = await AllocationService.get_student_active_registrations(session, student.id)
    if not registrations:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📝 Imtihonga yozilish", callback_data="stu_book_start")],
                [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home")],
            ]
        )
        if callback.message:
            await callback.message.edit_text(
                "📋 <b>Sizda faol imtihonlar qolmadi.</b>",
                reply_markup=kb,
                parse_mode="HTML",
            )
        return

    text = "📋 <b>Siz ro'yxatdan o'tgan imtihonlar:</b>\n\n"
    for idx, reg in enumerate(registrations, 1):
        d_str = reg.session.exam_date.strftime("%d.%m.%Y")
        t_str = reg.session.start_time.strftime("%H:%M")
        text += (
            f"<b>{idx}. 📚 Fan: {reg.session.subject.name}</b>\n"
            f"   📅 Sana: {d_str} | 🕑 Vaqt: {t_str}\n"
            f"   📍 Manzil: {reg.session.location.name}\n"
            f"   🚪 Xona: <b>{reg.room.name}</b> | 🪑 Stol: <b>{reg.seat_no}</b>\n\n"
        )

    if callback.message:
        await callback.message.edit_text(text, reply_markup=get_my_registrations_kb(registrations), parse_mode="HTML")


@my_exams_router.callback_query(F.data.startswith("stu_cancel:"))
async def prompt_cancel_registration(callback: CallbackQuery, session: AsyncSession) -> None:
    """Bekor qilishni so'rash"""
    await callback.answer()
    reg_id = int(callback.data.split(":")[1])

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Ha, bekor qilinsin", callback_data=f"stu_confirm_cancel:{reg_id}"),
                InlineKeyboardButton(text="⬅️ Orqaga", callback_data="stu_my_exams_cb"),
            ]
        ]
    )

    if callback.message:
        await callback.message.edit_text(
            "⚠️ <b>Haqiqatan ham ushbu imtihonga yozilishni bekor qilmoqchimisiz?</b>\n\n"
            "Joyingiz boshqa o'quvchilar uchun bo'shatiladi.",
            reply_markup=kb,
            parse_mode="HTML",
        )


@my_exams_router.callback_query(F.data.startswith("stu_confirm_cancel:"))
async def execute_cancel_registration(callback: CallbackQuery, session: AsyncSession) -> None:
    """Bekor qilishni amalga oshirish"""
    reg_id = int(callback.data.split(":")[1])
    student = await StudentService.get_student_by_telegram_id(session, callback.from_user.id)
    if not student:
        await callback.answer("O'quvchi topilmadi", show_alert=True)
        return

    success = await AllocationService.cancel_registration(session, registration_id=reg_id, student_id=student.id)
    if success:
        await callback.answer("Ro'yxatdan o'tish bekor qilindi!", show_alert=True)
    else:
        await callback.answer("Bekor qilishda xatolik yuz berdi.", show_alert=True)

    # Yangilangan ro'yxatga qaytish
    registrations = await AllocationService.get_student_active_registrations(session, student.id)
    if not registrations:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📝 Imtihonga yozilish", callback_data="stu_book_start")],
                [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home")],
            ]
        )
        if callback.message:
            await callback.message.edit_text(
                "✅ <b>Imtihonga yozilish bekor qilindi va joy bo'shatildi.</b>\n\nSizda hozircha faol imtihonlar yo'q.",
                reply_markup=kb,
                parse_mode="HTML",
            )
    else:
        text = "✅ <b>Imtihonga yozilish bekor qilindi!</b>\n\nQolgan faol imtihonlaringiz:\n\n"
        for idx, reg in enumerate(registrations, 1):
            d_str = reg.session.exam_date.strftime("%d.%m.%Y")
            t_str = reg.session.start_time.strftime("%H:%M")
            text += (
                f"<b>{idx}. 📚 Fan: {reg.session.subject.name}</b>\n"
                f"   📅 Sana: {d_str} | 🕑 Vaqt: {t_str}\n"
                f"   🚪 Xona: <b>{reg.room.name}</b> | 🪑 Stol: <b>{reg.seat_no}</b>\n\n"
            )
        if callback.message:
            await callback.message.edit_text(text, reply_markup=get_my_registrations_kb(registrations), parse_mode="HTML")
