import asyncio
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db.models.registration import Registration
from bot.keyboards.admin_kb import get_sessions_select_list_kb
from bot.middlewares.admin_check import IsAdminFilter
from bot.services.session_service import SessionService
from bot.states.admin_states import BroadcastStates

admin_broadcast_router = Router(name="admin_broadcast")
admin_broadcast_router.message.filter(IsAdminFilter())
admin_broadcast_router.callback_query.filter(IsAdminFilter())


@admin_broadcast_router.message(F.text == "📢 Xabar yuborish")
async def show_broadcast_sessions_select(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Xabar yuborish uchun seans tanlash"""
    await state.clear()
    sessions = await SessionService.get_all_active_sessions(session)
    if not sessions:
        await message.answer("⚠️ Hozircha birorta ham seans mavjud emas.")
        return

    await message.answer(
        "📢 <b>Xabar yuborish:</b>\n\nQaysi imtihonga yozilgan barcha o'quvchilarga xabar yubormoqchisiz? Seansni tanlang:",
        reply_markup=get_sessions_select_list_kb(sessions, prefix="adm_bc_start"),
        parse_mode="HTML",
    )


@admin_broadcast_router.callback_query(F.data.startswith("adm_bc_start:"))
async def start_broadcast(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Xabar matnini so'rash"""
    await callback.answer()
    sess_id = int(callback.data.split(":")[1])
    sess = await SessionService.get_session_by_id(session, sess_id)
    if not sess:
        if callback.message:
            await callback.message.edit_text("⚠️ Seans topilmadi.")
        return

    await state.update_data(broadcast_session_id=sess_id)
    await state.set_state(BroadcastStates.waiting_text)

    text = (
        f"📢 <b>Xabar yuborish</b>\n\n"
        f"Tanlangan seans: <b>{sess.subject.name} ({sess.exam_date.strftime('%d.%m.%Y')} {sess.start_time.strftime('%H:%M')})</b>\n\n"
        f"Ushbu seansga yozilgan barcha o'quvchilarga yuboriladigan xabar matnini kiriting:"
    )
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML")


@admin_broadcast_router.message(BroadcastStates.waiting_text)
async def process_broadcast_text(message: Message, state: FSMContext) -> None:
    """Xabar matni kiritildi, tasdiqlash so'raladi"""
    broadcast_text = (message.text or "").strip()
    if not broadcast_text:
        await message.answer("⚠️ Xabar matni bo'sh bo'lishi mumkin emas. Qaytadan kiriting:")
        return

    await state.update_data(broadcast_text=broadcast_text)
    await state.set_state(BroadcastStates.waiting_confirm)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, yuborilsin", callback_data="adm_bc_confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm_main"),
            ]
        ]
    )

    await message.answer(
        f"⚠️ <b>Xabarni tasdiqlang:</b>\n\n"
        f"<i>Xabar matni:</i>\n{broadcast_text}\n\n"
        f"Ushbu xabar seansga yozilgan barcha o'quvchilarga yuborilsinmi?",
        reply_markup=kb,
        parse_mode="HTML",
    )


@admin_broadcast_router.callback_query(F.data == "adm_bc_confirm")
async def execute_broadcast(callback: CallbackQuery, bot: Bot, session: AsyncSession, state: FSMContext) -> None:
    """Xabarni barcha o'quvchilarga tarqatish"""
    await callback.answer("Xabar yuborilmoqda...", show_alert=False)
    data = await state.get_data()
    sess_id = data.get("broadcast_session_id")
    broadcast_text = data.get("broadcast_text")
    await state.clear()

    # O'quvchilarni olish
    query = (
        select(Registration)
        .where(
            Registration.session_id == sess_id,
            Registration.status == "active",
        )
        .options(selectinload(Registration.student))
    )
    registrations = list((await session.execute(query)).scalars().all())

    if not registrations:
        if callback.message:
            await callback.message.edit_text(
                "ℹ️ Ushbu seansga hozircha birorta ham o'quvchi ro'yxatdan o'tmagan. Xabar yuborilmadi.",
                parse_mode="HTML",
            )
        return

    success_count = 0
    fail_count = 0

    formatted_msg = (
        f"📢 <b>O'QUV MARKAZIDAN BILDIRISHNOMA:</b>\n\n"
        f"{broadcast_text}"
    )

    for reg in registrations:
        if reg.student and reg.student.telegram_id:
            try:
                await bot.send_message(
                    chat_id=reg.student.telegram_id,
                    text=formatted_msg,
                    parse_mode="HTML",
                )
                success_count += 1
                await asyncio.sleep(0.05)  # Telegram flood control
            except Exception:
                fail_count += 1

    result_text = (
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"📤 Muvaffaqiyatli yetkazildi: <b>{success_count} ta</b>\n"
        f"⚠️ Yetkazib bo'lmadi: {fail_count} ta"
    )

    if callback.message:
        await callback.message.edit_text(result_text, parse_mode="HTML")
