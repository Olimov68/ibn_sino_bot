from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin_kb import get_admin_main_menu_kb
from bot.keyboards.student_kb import get_student_main_menu_kb
from bot.services.admin_service import AdminService
from bot.services.channel_service import ChannelService
from bot.services.student_service import StudentService
from bot.states.student_states import StudentRegistrationStates

common_router = Router(name="common_router")


@common_router.message(CommandStart())
async def handle_start_command(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """
    /start buyrug'i:
    1. Admin bo'lsa -> to'g'ridan-to'g'ri Admin panelini ochadi.
    2. Ro'yxatdan o'tgan o'quvchi bo'lsa -> O'quvchi menyusini ochadi.
    3. Yangi foydalanuvchi bo'lsa -> Ro'yxatdan o'tish jarayonini boshlaydi (FSM).
    """
    await state.clear()
    user_id = message.from_user.id
    is_admin = await AdminService.is_admin(session, user_id)

    if is_admin:
        await message.answer(
            f"👋 Assalomu alaykum, Hurmatli Administrator!\n\n"
            f"🛠 <b>@ibnsinoschoolbot Boshqaruv paneliga xush kelibsiz.</b>\n"
            f"Quyidagi menyu orqali barcha jarayonlarni boshqarishingiz mumkin:",
            reply_markup=get_admin_main_menu_kb(),
            parse_mode="HTML",
        )
        return

    # O'quvchini tekshirish
    student = await StudentService.get_student_by_telegram_id(session, user_id)
    if student and student.phone and student.grade:
        await message.answer(
            f"👋 Assalomu alaykum, <b>{student.full_name}</b>!\n\n"
            f"📚 <b>Ibn Sino maktabi</b> imtihon botiga xush kelibsiz.\n"
            f"Kerakli bo'limni tanlang:",
            reply_markup=get_student_main_menu_kb(is_admin=False),
            parse_mode="HTML",
        )
    else:
        # Yangi o'quvchini ro'yxatdan o'tkazishni boshlash
        await state.set_state(StudentRegistrationStates.waiting_full_name)
        await message.answer(
            "👋 Assalomu alaykum!\n\n"
            "<b>Ibn Sino maktabi</b> haftalik mock imtihonlar botiga xush kelibsiz!\n\n"
            "Ro'yxatdan o'tish uchun, iltimos, <b>Ism va Familiyangizni</b> kiriting:\n"
            "<i>(Masalan: Ali Valiyev)</i>",
            parse_mode="HTML",
        )


@common_router.message(F.text == "🔙 O'quvchi rejimiga o'tish")
async def switch_to_student_mode(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Adminning o'quvchi rejimiga o'tishi"""
    await state.clear()
    is_admin = await AdminService.is_admin(session, message.from_user.id)
    await message.answer(
        "🔄 <b>O'quvchi rejimiga o'tdingiz.</b>\n\nBu yerda botning o'quvchilar uchun ko'rinishini tekshirishingiz mumkin:",
        reply_markup=get_student_main_menu_kb(is_admin=is_admin),
        parse_mode="HTML",
    )


@common_router.message(F.text == "🛠 Admin paneliga qaytish")
async def switch_back_to_admin_mode(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Adminning qayta boshqaruv paneliga qaytishi"""
    await state.clear()
    is_admin = await AdminService.is_admin(session, message.from_user.id)
    if not is_admin:
        await message.answer("⚠️ Siz administrator emassiz.")
        return

    await message.answer(
        "🛠 <b>Boshqaruv paneli (Admin):</b>",
        reply_markup=get_admin_main_menu_kb(),
        parse_mode="HTML",
    )


@common_router.message(F.text == "🏠 Asosiy menyu")
@common_router.callback_query(F.data == "stu_home")
async def handle_student_home(event: Message | CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """O'quvchi asosiy menyusiga qaytish"""
    await state.clear()
    user_id = event.from_user.id
    is_admin = await AdminService.is_admin(session, user_id)

    text = "🏠 <b>Asosiy menyu:</b>\n\nQuyidagi amallardan birini tanlang:"
    kb = get_student_main_menu_kb(is_admin=is_admin)

    if isinstance(event, CallbackQuery):
        await event.answer()
        if event.message:
            try:
                await event.message.delete()
            except Exception:
                pass
            await event.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@common_router.callback_query(F.data == "sub_check")
async def handle_check_subscription(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Majburiy kanal obunasini tekshirish callbacki"""
    user_id = callback.from_user.id
    is_subscribed, unsubscribed = await ChannelService.check_user_subscription(
        bot=bot,
        session=session,
        user_id=user_id,
    )

    if not is_subscribed:
        await callback.answer(
            "❌ Siz hali barcha kanallarga a'zo bo'lmadingiz! Iltimos, yuqoridagi kanalga obuna bo'lib, qayta tekshiring.",
            show_alert=True,
        )
        return

    await callback.answer("✅ Rahmat! Obuna muvaffaqiyatli tasdiqlandi.", show_alert=True)
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass

    # Endi foydalanuvchini holatiga qarab tegishli menyuga o'tkazish
    is_admin = await AdminService.is_admin(session, user_id)
    if is_admin:
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "👋 Assalomu alaykum, Hurmatli Administrator!\n\n"
                "🛠 <b>@ibnsinoschoolbot Boshqaruv paneliga xush kelibsiz.</b>\n"
                "Quyidagi menyu orqali barcha jarayonlarni boshqarishingiz mumkin:"
            ),
            reply_markup=get_admin_main_menu_kb(),
            parse_mode="HTML",
        )
        return

    student = await StudentService.get_student_by_telegram_id(session, user_id)
    if student and student.phone and student.grade:
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                f"👋 Assalomu alaykum, <b>{student.full_name}</b>!\n\n"
                "📚 <b>Ibn Sino maktabi</b> imtihon botiga xush kelibsiz.\n"
                "Kerakli bo'limni tanlang:"
            ),
            reply_markup=get_student_main_menu_kb(is_admin=False),
            parse_mode="HTML",
        )
    else:
        await state.set_state(StudentRegistrationStates.waiting_full_name)
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "👋 Assalomu alaykum!\n\n"
                "<b>Ibn Sino maktabi</b> haftalik mock imtihonlar botiga xush kelibsiz!\n\n"
                "Ro'yxatdan o'tish uchun, iltimos, <b>Ism va Familiyangizni</b> kiriting:\n"
                "<i>(Masalan: Ali Valiyev)</i>"
            ),
            parse_mode="HTML",
        )


