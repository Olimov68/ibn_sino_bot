import logging
from typing import Any, Awaitable, Callable, Dict, Union
from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.services.admin_service import AdminService
from bot.services.channel_service import ChannelService

logger = logging.getLogger("ibnsinobot.subscription_middleware")


def get_subscription_prompt_kb(unsubscribed_channels) -> InlineKeyboardMarkup:
    """A'zo bo'linmagan kanallar ro'yxati va tekshirish tugmasi"""
    kb = []
    for ch in unsubscribed_channels:
        kb.append([InlineKeyboardButton(text=f"📢 {ch.title}", url=ch.invite_link)])
    kb.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="sub_check")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


class SubscriptionMiddleware(BaseMiddleware):
    """
    Har bir xabar va tugma bosilishida majburiy kanal obunasini tekshiruvchi middleware.
    Agar foydalanuvchi obuna bo'lmagan bo'lsa (yoki keyinroq chiqib ketgan bo'lsa),
    amallarni to'xtatadi va obuna bo'lishni talab qiladi.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Faqat Message va CallbackQuery larni tekshiramiz
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        user = getattr(event, "from_user", None)
        if not user or user.is_bot:
            return await handler(event, data)

        # Agar callback sub_check bo'lsa, uni to'g'ridan-to'g'ri handlerga o'tkazamiz
        if isinstance(event, CallbackQuery) and event.data == "sub_check":
            return await handler(event, data)

        # Adminlarni tekshiruvdan ozod qilish
        session: AsyncSession = data.get("session")
        if user.id in settings.admin_ids_list:
            return await handler(event, data)

        if session:
            is_admin = await AdminService.is_admin(session, user.id)
            if is_admin:
                return await handler(event, data)

        # Bot obyektini olish
        bot: Bot = data.get("bot")
        if not bot or not session:
            return await handler(event, data)

        # Majburiy kanallarga a'zolikni tekshirish
        is_subscribed, unsubscribed = await ChannelService.check_user_subscription(
            bot=bot,
            session=session,
            user_id=user.id,
        )

        if is_subscribed:
            return await handler(event, data)

        # Agar obuna bo'lmagan bo'lsa
        sub_kb = get_subscription_prompt_kb(unsubscribed)
        prompt_text = (
            "⚠️ <b>Hurmatli foydalanuvchi!</b>\n\n"
            "Botdan to'liq foydalanish uchun quyidagi rasmiy kanalimizga a'zo bo'lishingiz shart.\n\n"
            "Kanalga a'zo bo'lgach, <b>«✅ Obunani tekshirish»</b> tugmasini bosing:"
        )

        if isinstance(event, CallbackQuery):
            await event.answer("⚠️ Botdan foydalanish uchun avval kanalga a'zo bo'ling!", show_alert=True)
            if event.message:
                try:
                    await event.message.edit_text(prompt_text, reply_markup=sub_kb, parse_mode="HTML")
                except Exception:
                    await event.message.answer(prompt_text, reply_markup=sub_kb, parse_mode="HTML")
        elif isinstance(event, Message):
            await event.answer(prompt_text, reply_markup=sub_kb, parse_mode="HTML")

        # Keyingi handlerlar bajarilmaydi
        return None
