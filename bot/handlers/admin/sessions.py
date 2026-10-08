import datetime
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin_kb import (
    get_locations_selection_kb,
    get_session_item_kb,
    get_sessions_manage_kb,
    get_subjects_selection_kb,
)
from bot.middlewares.admin_check import IsAdminFilter
from bot.services.location_service import LocationService
from bot.services.session_service import SessionService
from bot.services.subject_service import SubjectService
from bot.states.admin_states import SessionStates

admin_sessions_router = Router(name="admin_sessions")
admin_sessions_router.message.filter(IsAdminFilter())
admin_sessions_router.callback_query.filter(IsAdminFilter())


@admin_sessions_router.message(F.text == "🗓 Imtihon seanslari")
async def show_sessions_menu(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Imtihon seanslari ro'yxati"""
    await state.clear()
    sessions = await SessionService.get_all_active_sessions(session)
    await message.answer(
        "🗓 <b>Imtihon seanslari boshqaruvi:</b>\n\nQuyidagi seanslardan birini tanlang yoki yangi seans yarating:",
        reply_markup=get_sessions_manage_kb(sessions),
        parse_mode="HTML",
    )


@admin_sessions_router.callback_query(F.data == "adm_sess_list")
async def show_sessions_cb(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Seanslar ro'yxatiga qaytish"""
    await state.clear()
    await callback.answer()
    sessions = await SessionService.get_all_active_sessions(session)
    if callback.message:
        await callback.message.edit_text(
            "🗓 <b>Imtihon seanslari boshqaruvi:</b>\n\nSeanslar ro'yxati:",
            reply_markup=get_sessions_manage_kb(sessions),
            parse_mode="HTML",
        )


@admin_sessions_router.callback_query(F.data == "adm_sess_add")
async def start_add_session(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Yangi seans yaratish: 1-bosqich - Fanni tanlash"""
    await callback.answer()
    subjects = await SubjectService.get_subjects(session)
    if not subjects:
        if callback.message:
            await callback.message.edit_text("⚠️ Avval 📚 Fanlar bo'limidan kamida bitta fan qo'shing.")
        return

    await state.set_state(SessionStates.waiting_subject)
    if callback.message:
        await callback.message.edit_text(
            "🗓 <b>Yangi imtihon seansi yaratish</b>\n\n1️⃣ Imtihon o'tkaziladigan fanni tanlang:",
            reply_markup=get_subjects_selection_kb(subjects),
            parse_mode="HTML",
        )


@admin_sessions_router.callback_query(F.data.startswith("adm_sel_sub:"))
async def select_session_subject(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """2-bosqich - Manzilni tanlash"""
    await callback.answer()
    sub_id = int(callback.data.split(":")[1])
    await state.update_data(subject_id=sub_id)

    locations = await LocationService.get_locations(session)
    if not locations:
        if callback.message:
            await callback.message.edit_text("⚠️ Avval 📍 Manzillar bo'limidan manzil qo'shing.")
        return

    await state.set_state(SessionStates.waiting_location)
    if callback.message:
        await callback.message.edit_text(
            "2️⃣ Imtihon o'tkaziladigan bino/manzilni tanlang:",
            reply_markup=get_locations_selection_kb(locations),
            parse_mode="HTML",
        )


@admin_sessions_router.callback_query(F.data.startswith("adm_sel_loc:"))
async def select_session_location(callback: CallbackQuery, state: FSMContext) -> None:
    """3-bosqich - Sanani kiritish"""
    await callback.answer()
    loc_id = int(callback.data.split(":")[1])
    await state.update_data(location_id=loc_id)

    await state.set_state(SessionStates.waiting_date)
    if callback.message:
        await callback.message.edit_text(
            "3️⃣ Imtihon sanasini kiriting:\n<i>Format: KUN.OY.YIL (Masalan: 25.10.2026)</i>",
            parse_mode="HTML",
        )


@admin_sessions_router.message(SessionStates.waiting_date)
async def process_session_date(message: Message, state: FSMContext) -> None:
    """Sana tekshirildi"""
    text = (message.text or "").strip()
    try:
        exam_date = datetime.datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("⚠️ Sana formati noto'g'ri! Iltimos, <b>KUN.OY.YIL</b> shaklida kiriting (Masalan: 25.10.2026):", parse_mode="HTML")
        return

    await state.update_data(exam_date=text)
    await state.set_state(SessionStates.waiting_time)
    await message.answer(
        f"📅 Sana: <b>{text}</b>\n\n4️⃣ Endi imtihon boshlanish vaqtini kiriting:\n<i>Format: SOAT:DAQIQALAR (Masalan: 09:00 yoki 14:30)</i>",
        parse_mode="HTML",
    )


@admin_sessions_router.message(SessionStates.waiting_time)
async def process_session_time(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Vaqt tekshirildi va seans yaratildi"""
    text = (message.text or "").strip()
    try:
        start_time = datetime.datetime.strptime(text, "%H:%M").time()
    except ValueError:
        await message.answer("⚠️ Vaqt formati noto'g'ri! Iltimos, <b>SOAT:DAQIQA</b> shaklida kiriting (Masalan: 09:00):", parse_mode="HTML")
        return

    data = await state.get_data()
    sub_id = data.get("subject_id")
    loc_id = data.get("location_id")
    exam_date = datetime.datetime.strptime(data.get("exam_date"), "%d.%m.%Y").date()
    await state.clear()

    exam_session = await SessionService.create_session(
        session,
        subject_id=sub_id,
        location_id=loc_id,
        exam_date=exam_date,
        start_time=start_time,
    )
    full_session = await SessionService.get_session_by_id(session, exam_session.id)
    sessions = await SessionService.get_all_active_sessions(session)

    await message.answer(
        f"🎉 <b>Yangi imtihon seansi muvaffaqiyatli yaratildi!</b>\n\n"
        f"📚 Fan: <b>{full_session.subject.name}</b>\n"
        f"📍 Bino: {full_session.location.name}\n"
        f"📅 Sana: {full_session.exam_date.strftime('%d.%m.%Y')}\n"
        f"🕑 Boshlanish vaqti: {full_session.start_time.strftime('%H:%M')}\n"
        f"🟢 Holati: Ochiq",
        reply_markup=get_sessions_manage_kb(sessions),
        parse_mode="HTML",
    )


@admin_sessions_router.callback_query(F.data.startswith("adm_sess_view:"))
async def view_session_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    """Seans tafsilotlarini ko'rish"""
    await callback.answer()
    sess_id = int(callback.data.split(":")[1])
    sess = await SessionService.get_session_by_id(session, sess_id)
    if not sess:
        if callback.message:
            await callback.message.edit_text("⚠️ Seans topilmadi.")
        return

    cap_info = await SessionService.get_session_capacity_info(session, sess.id)
    text = (
        f"🗓 <b>Imtihon seansi tafsilotlari:</b>\n\n"
        f"📚 Fan: <b>{sess.subject.name}</b>\n"
        f"📍 Manzil: {sess.location.name} ({sess.location.address})\n"
        f"📅 Sana: {sess.exam_date.strftime('%d.%m.%Y')}\n"
        f"🕑 Vaqt: {sess.start_time.strftime('%H:%M')}\n"
        f"⚙️ Holati: <b>{sess.status.upper()}</b>\n\n"
        f"🪑 Jami joy: {cap_info['total']} ta\n"
        f"👥 Band joylar: {cap_info['registered']} ta\n"
        f"🟢 Bo'sh joylar: {cap_info['remaining']} ta\n"
    )
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_session_item_kb(sess.id, is_open=(sess.status == "open")),
            parse_mode="HTML",
        )


@admin_sessions_router.callback_query(F.data.startswith("adm_sess_close:"))
async def close_session_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """Seansni yopish"""
    sess_id = int(callback.data.split(":")[1])
    closed = await SessionService.close_session(session, sess_id)
    await callback.answer("Seans yopildi!" if closed else "Topilmadi", show_alert=True)

    sess = await SessionService.get_session_by_id(session, sess_id)
    if sess and callback.message:
        await callback.message.edit_text(
            f"🔒 <b>Seans yopildi!</b>\n\n📚 Fan: {sess.subject.name}\n📅 Sana: {sess.exam_date.strftime('%d.%m.%Y')}",
            reply_markup=get_session_item_kb(sess.id, is_open=False),
            parse_mode="HTML",
        )
