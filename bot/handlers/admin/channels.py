from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin_kb import (
    get_cancel_channel_add_kb,
    get_channel_item_kb,
    get_channels_manage_kb,
)
from bot.middlewares.admin_check import IsAdminFilter
from bot.services.channel_service import ChannelService
from bot.states.admin_states import ChannelStates

admin_channels_router = Router(name="admin_channels")
admin_channels_router.message.filter(IsAdminFilter())
admin_channels_router.callback_query.filter(IsAdminFilter())


@admin_channels_router.message(F.text == "📢 Majburiy obuna")
@admin_channels_router.callback_query(F.data == "adm_ch_list")
async def show_channels_list(event: Message | CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Majburiy kanallar ro'yxati"""
    await state.clear()
    channels = await ChannelService.get_all_channels(session)

    text = (
        "📢 <b>Majburiy a'zolik kanallari boshqaruvi</b>\n\n"
        "Foydalanuvchilar botdan foydalanishi uchun quyidagi kanallarga obuna bo'lishi shart.\n\n"
        "Kanallar holati:\n"
        "🟢 — Faol (majburiy tekshiriladi)\n"
        "🔴 — Nofaol (tekshirilmaydi)\n\n"
        f"Jami kanallar: <b>{len(channels)} ta</b>"
    )

    kb = get_channels_manage_kb(channels)

    if isinstance(event, CallbackQuery):
        await event.answer()
        if event.message:
            await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@admin_channels_router.callback_query(F.data.startswith("adm_ch_view:"))
async def view_channel_details(callback: CallbackQuery, session: AsyncSession) -> None:
    """Kanal tafsilotlari"""
    await callback.answer()
    channel_id = int(callback.data.split(":")[1])
    channel = await ChannelService.get_channel_by_id(session, channel_id)

    if not channel:
        await callback.answer("⚠️ Kanal topilmadi!", show_alert=True)
        return

    status_str = "🟢 Faol (tekshirilmoqda)" if channel.is_active else "🔴 Nofaol"
    text = (
        f"📢 <b>Kanal: {channel.title}</b>\n\n"
        f"🆔 <b>Kanal ID / Username:</b> <code>{channel.channel_id}</code>\n"
        f"🔗 <b>Havola:</b> {channel.invite_link}\n"
        f"⚙️ <b>Holat:</b> {status_str}\n"
        f"📅 <b>Qo'shilgan sana:</b> {channel.created_at.strftime('%d.%m.%Y %H:%M') if channel.created_at else '-'}\n"
    )

    kb = get_channel_item_kb(channel)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@admin_channels_router.callback_query(F.data.startswith("adm_ch_toggle:"))
async def toggle_channel_status(callback: CallbackQuery, session: AsyncSession) -> None:
    """Kanal holatini o'zgartirish (faol / nofaol)"""
    channel_id = int(callback.data.split(":")[1])
    channel = await ChannelService.toggle_channel_status(session, channel_id)

    if not channel:
        await callback.answer("⚠️ Kanal topilmadi!", show_alert=True)
        return

    new_status = "🟢 Faollashtirildi" if channel.is_active else "🔴 Nofaol qilindi"
    await callback.answer(f"Kanal holati: {new_status}")

    # Sahifani yangilash
    await view_channel_details(callback, session)


@admin_channels_router.callback_query(F.data.startswith("adm_ch_del:"))
async def delete_channel(callback: CallbackQuery, session: AsyncSession) -> None:
    """Kanalni o'chirish"""
    channel_id = int(callback.data.split(":")[1])
    success = await ChannelService.delete_channel(session, channel_id)

    if success:
        await callback.answer("🗑 Kanal o'chirildi!", show_alert=True)
    else:
        await callback.answer("⚠️ Kanal topilmadi!", show_alert=True)

    channels = await ChannelService.get_all_channels(session)
    text = (
        "📢 <b>Majburiy a'zolik kanallari boshqaruvi</b>\n\n"
        f"Jami kanallar: <b>{len(channels)} ta</b>"
    )
    if callback.message:
        await callback.message.edit_text(text, reply_markup=get_channels_manage_kb(channels), parse_mode="HTML")


@admin_channels_router.callback_query(F.data == "adm_ch_add")
async def start_add_channel(callback: CallbackQuery, state: FSMContext) -> None:
    """Yangi kanal qo'shish jarayonini boshlash"""
    await callback.answer()
    await state.set_state(ChannelStates.waiting_channel_identifier)

    text = (
        "➕ <b>Yangi majburiy kanal qo'shish</b>\n\n"
        "Iltimos, kanalning <b>username</b> (@kanal_nomi) yoki <b>ID</b> sini yuboring:\n"
        "<i>(Masalan: @ibn_sino_maktabi yoki -1001234567890)</i>\n\n"
        "⚠️ <b>Muhim eslatma:</b> Bot ushbu kanalga <b>Administrator</b> qilib qo'shilgan bo'lishi shart!"
    )
    if callback.message:
        await callback.message.edit_text(text, reply_markup=get_cancel_channel_add_kb(), parse_mode="HTML")


@admin_channels_router.message(ChannelStates.waiting_channel_identifier)
async def process_channel_identifier(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    """Kanal identifikatorini qayta ishlash"""
    raw_text = (message.text or "").strip()
    if not raw_text:
        await message.answer("⚠️ Iltimos, kanal username yoki ID sini matn sifatida yuboring:")
        return

    channel_id = raw_text
    chat_target: int | str = channel_id
    if channel_id.startswith("-") and channel_id[1:].isdigit():
        chat_target = int(channel_id)

    # Bot orqali Telegram API dan chat ma'lumotlarini tekshirish
    try:
        chat = await bot.get_chat(chat_target)
        title = chat.title or "Telegram Kanal"
        username = f"@{chat.username}" if chat.username else None
        invite_link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)

        if invite_link:
            # Barcha ma'lumotlar avtomatik olindi
            channel = await ChannelService.add_channel(
                session=session,
                channel_id=channel_id,
                title=title,
                invite_link=invite_link,
                username=username,
            )
            await state.clear()
            channels = await ChannelService.get_all_channels(session)
            await message.answer(
                f"✅ <b>Kanal muvaffaqiyatli qo'shildi!</b>\n\n"
                f"📢 <b>Nomi:</b> {channel.title}\n"
                f"🆔 <b>ID / Username:</b> <code>{channel.channel_id}</code>\n"
                f"🔗 <b>Havola:</b> {channel.invite_link}",
                reply_markup=get_channels_manage_kb(channels),
                parse_mode="HTML",
            )
            return
        else:
            # Havola topilmadi (masalan, private kanal)
            await state.update_data(channel_id=channel_id, title=title, username=username)
            await state.set_state(ChannelStates.waiting_invite_link)
            await message.answer(
                f"📢 Kanal nomi aniqlandi: <b>{title}</b>\n\n"
                "Iltimos, kanalga a'zo bo'lish uchun <b>taklif havolasini (invite link)</b> kiriting:\n"
                "<i>(Masalan: https://t.me/+AbCdEfGhIjK)</i>",
                reply_markup=get_cancel_channel_add_kb(),
                parse_mode="HTML",
            )
            return
    except Exception:
        # Bot kanalda yo'q yoki xususiy kanal
        await state.update_data(channel_id=channel_id)
        await state.set_state(ChannelStates.waiting_channel_title)
        await message.answer(
            "⚠️ Kanal ma'lumotlarini avtomatik yuklab bo'lmadi.\n"
            "<i>(Bot kanalda admin ekanligiga ishonch hosil qiling)</i>\n\n"
            "Iltimos, kanalning <b>nomini</b> qo'lda kiriting:\n"
            "<i>(Masalan: Ibn Sino Maktabi)</i>",
            reply_markup=get_cancel_channel_add_kb(),
            parse_mode="HTML",
        )


@admin_channels_router.message(ChannelStates.waiting_channel_title)
async def process_channel_title(message: Message, state: FSMContext) -> None:
    """Kanal nomini qabul qilish"""
    title = (message.text or "").strip()
    if not title:
        await message.answer("⚠️ Kanal nomi bo'sh bo'lishi mumkin emas. Qayta kiriting:")
        return

    await state.update_data(title=title)
    await state.set_state(ChannelStates.waiting_invite_link)
    await message.answer(
        "Endi kanalning <b>taklif havolasini (link)</b> kiriting:\n"
        "<i>(Masalan: https://t.me/ibn_sino_maktabi yoki https://t.me/+abcdef)</i>",
        reply_markup=get_cancel_channel_add_kb(),
        parse_mode="HTML",
    )


@admin_channels_router.message(ChannelStates.waiting_invite_link)
async def process_channel_link(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """Kanal havolasini qabul qilish va saqlash"""
    link = (message.text or "").strip()
    if not link or not (link.startswith("http://") or link.startswith("https://") or link.startswith("t.me/")):
        await message.answer("⚠️ Iltimos, to'g'ri havola kiriting (https://t.me/...):")
        return

    if not link.startswith("http"):
        link = f"https://{link}"

    data = await state.get_data()
    channel_id = data.get("channel_id")
    title = data.get("title", "Telegram Kanal")
    username = data.get("username")

    channel = await ChannelService.add_channel(
        session=session,
        channel_id=channel_id,
        title=title,
        invite_link=link,
        username=username,
    )

    await state.clear()
    channels = await ChannelService.get_all_channels(session)
    await message.answer(
        f"✅ <b>Kanal muvaffaqiyatli saqlandi!</b>\n\n"
        f"📢 <b>Nomi:</b> {channel.title}\n"
        f"🆔 <b>ID:</b> <code>{channel.channel_id}</code>\n"
        f"🔗 <b>Havola:</b> {channel.invite_link}",
        reply_markup=get_channels_manage_kb(channels),
        parse_mode="HTML",
    )
