import re
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.student_kb import get_grades_kb, get_phone_request_kb, get_profile_edit_kb
from bot.services.student_service import StudentService
from bot.states.student_states import StudentProfileStates

profile_router = Router(name="student_profile")


@profile_router.message(F.text == "👤 Profilim")
async def show_profile_menu(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Foydalanuvchi profili"""
    await state.clear()
    student = await StudentService.get_student_by_telegram_id(session, message.from_user.id)
    if not student:
        await message.answer("⚠️ Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
        return

    text = (
        f"👤 <b>SIZNING PROFILINGIZ</b>\n\n"
        f"🏷 <b>F.I.Sh:</b> {student.full_name}\n"
        f"📱 <b>Telefon:</b> {student.phone or 'Kiritilmagan'}\n"
        f"🎓 <b>Sinf:</b> {f'{student.grade}-sinf' if student.grade else 'Kiritilmagan'}\n"
        f"📅 <b>Ro'yxatdan o'tgan:</b> {student.created_at.strftime('%d.%m.%Y')}\n\n"
        f"Ma'lumotlaringizni yangilash uchun quyidagi tugmalardan foydalanishingiz mumkin:"
    )
    await message.answer(text, reply_markup=get_profile_edit_kb(), parse_mode="HTML")


@profile_router.callback_query(F.data == "stu_prof_edit_name")
async def start_edit_name(callback: CallbackQuery, state: FSMContext) -> None:
    """Ismni o'zgartirish"""
    await callback.answer()
    await state.set_state(StudentProfileStates.waiting_edit_name)
    if callback.message:
        await callback.message.edit_text(
            "✏️ <b>Ism va familiyangizni yangilang:</b>\n<i>(Masalan: Saidov Jasur)</i>",
            parse_mode="HTML",
        )


@profile_router.message(StudentProfileStates.waiting_edit_name)
async def process_edit_name(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Yangi ism saqlandi"""
    new_name = (message.text or "").strip()
    if len(new_name) < 4:
        await message.answer("⚠️ Ism juda qisqa. Qaytadan kiriting:")
        return

    await state.clear()
    student = await StudentService.update_student(session, telegram_id=message.from_user.id, full_name=new_name)
    await message.answer(
        f"✅ <b>Ismingiz muvaffaqiyatli yangilandi:</b> {student.full_name}",
        reply_markup=get_profile_edit_kb(),
        parse_mode="HTML",
    )


@profile_router.callback_query(F.data == "stu_prof_edit_phone")
async def start_edit_phone(callback: CallbackQuery, state: FSMContext) -> None:
    """Telefonni o'zgartirish"""
    await callback.answer()
    await state.set_state(StudentProfileStates.waiting_edit_phone)
    if callback.message:
        await callback.message.answer(
            "📱 Yangi telefon raqamingizni yuboring yoki yozing (+998901234567):",
            reply_markup=get_phone_request_kb(),
        )


@profile_router.message(StudentProfileStates.waiting_edit_phone)
async def process_edit_phone(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Yangi telefon saqlandi"""
    phone = message.contact.phone_number if message.contact else (message.text or "").strip()
    cleaned_phone = re.sub(r"[^\d+]", "", phone)
    if not cleaned_phone.startswith("+"):
        cleaned_phone = "+" + cleaned_phone

    if len(cleaned_phone) < 9:
        await message.answer("⚠️ Telefon raqami noto'g'ri. Qaytadan kiriting:")
        return

    await state.clear()
    student = await StudentService.update_student(session, telegram_id=message.from_user.id, phone=cleaned_phone)
    await message.answer(
        f"✅ <b>Telefon raqamingiz yangilandi:</b> {student.phone}",
        reply_markup=get_profile_edit_kb(),
        parse_mode="HTML",
    )


@profile_router.callback_query(F.data == "stu_prof_edit_grade")
async def start_edit_grade(callback: CallbackQuery, state: FSMContext) -> None:
    """Sinfni o'zgartirish"""
    await callback.answer()
    await state.set_state(StudentProfileStates.waiting_edit_grade)
    if callback.message:
        await callback.message.edit_text(
            "🎓 <b>O'quv sinfingizni tanlang:</b>",
            reply_markup=get_grades_kb(),
            parse_mode="HTML",
        )


@profile_router.callback_query(StudentProfileStates.waiting_edit_grade, F.data.startswith("grade:"))
async def process_edit_grade(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Yangi sinf saqlandi"""
    await callback.answer()
    grade = int(callback.data.split(":")[1])
    await state.clear()

    student = await StudentService.update_student(session, telegram_id=callback.from_user.id, grade=grade)
    if callback.message:
        await callback.message.edit_text(
            f"✅ <b>Sinfingiz yangilandi:</b> {student.grade}-sinf",
            reply_markup=get_profile_edit_kb(),
            parse_mode="HTML",
        )
