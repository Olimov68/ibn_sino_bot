import re
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.student_kb import (
    get_grades_kb,
    get_phone_request_kb,
    get_student_main_menu_kb,
)
from bot.services.admin_service import AdminService
from bot.services.student_service import StudentService
from bot.states.student_states import StudentRegistrationStates

student_reg_router = Router(name="student_registration")


@student_reg_router.message(StudentRegistrationStates.waiting_full_name)
async def process_reg_full_name(message: Message, state: FSMContext) -> None:
    """Ism va familiya kiritildi"""
    full_name = (message.text or "").strip()
    if len(full_name) < 4 or " " not in full_name:
        await message.answer(
            "⚠️ Iltimos, to'liq ism va familiyangizni oraliq masofa (probel) bilan kiriting:\n<i>(Masalan: Saidov Jasur)</i>",
            parse_mode="HTML",
        )
        return

    await state.update_data(full_name=full_name)
    await state.set_state(StudentRegistrationStates.waiting_phone)

    await message.answer(
        f"✅ Rahmat, <b>{full_name}</b>!\n\n"
        f"📱 Endi telefon raqamingizni pastdagi <b>«📱 Telefon raqamimni yuborish»</b> tugmasi orqali yuboring yoki yozma shaklda kiriting (+998901234567):",
        reply_markup=get_phone_request_kb(),
        parse_mode="HTML",
    )


@student_reg_router.message(StudentRegistrationStates.waiting_phone)
async def process_reg_phone(message: Message, state: FSMContext) -> None:
    """Telefon raqami kiritildi (kontakt yoki matn orqali)"""
    phone = ""
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        phone = message.text.strip()

    # Raqamni tozalash
    cleaned_phone = re.sub(r"[^\d+]", "", phone)
    if not cleaned_phone.startswith("+"):
        cleaned_phone = "+" + cleaned_phone

    if len(cleaned_phone) < 9:
        await message.answer(
            "⚠️ Telefon raqami noto'g'ri kiritildi. Iltimos, tugma orqali yoki +998901234567 formatida kiriting:",
            reply_markup=get_phone_request_kb(),
        )
        return

    await state.update_data(phone=cleaned_phone)
    await state.set_state(StudentRegistrationStates.waiting_grade)

    await message.answer(
        f"📱 Telefon: <b>{cleaned_phone}</b>\n\n"
        f"🎓 Nechanchi sinfda o'qiysiz? Quyidagi sinflardan birini tanlang:",
        reply_markup=get_grades_kb(),
        parse_mode="HTML",
    )


@student_reg_router.callback_query(StudentRegistrationStates.waiting_grade, F.data.startswith("grade:"))
async def process_reg_grade(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Sinf tanlandi va o'quvchi ma'lumotlar bazasiga saqlandi"""
    await callback.answer()
    grade = int(callback.data.split(":")[1])

    data = await state.get_data()
    full_name = data.get("full_name")
    phone = data.get("phone")
    await state.clear()

    user_id = callback.from_user.id
    student = await StudentService.get_or_create_student(
        session,
        telegram_id=user_id,
        full_name=full_name,
        phone=phone,
        grade=grade,
    )

    is_admin = await AdminService.is_admin(session, user_id)

    if callback.message:
        await callback.message.delete()

    await callback.message.answer(
        f"🎉 <b>Muvaffaqiyatli ro'yxatdan o'tdingiz!</b>\n\n"
        f"👤 F.I.Sh: <b>{student.full_name}</b>\n"
        f"📱 Telefon: <b>{student.phone}</b>\n"
        f"🎓 Sinf: <b>{student.grade}-sinf</b>\n\n"
        f"Endi haftalik mock imtihonlarga bemalol yozilishingiz mumkin! 👇",
        reply_markup=get_student_main_menu_kb(is_admin=is_admin),
        parse_mode="HTML",
    )
