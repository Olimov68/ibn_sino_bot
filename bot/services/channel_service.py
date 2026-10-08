import logging
from typing import List, Optional, Tuple
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.channel import MandatoryChannel

logger = logging.getLogger("ibnsinobot.channel_service")


class ChannelService:
    """Majburiy a'zolik kanallari bilan ishlash xizmati"""

    @classmethod
    async def get_active_channels(cls, session: AsyncSession) -> List[MandatoryChannel]:
        """Barcha faol majburiy kanallarni olish"""
        result = await session.execute(
            select(MandatoryChannel).where(MandatoryChannel.is_active == True).order_by(MandatoryChannel.id)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_all_channels(cls, session: AsyncSession) -> List[MandatoryChannel]:
        """Barcha majburiy kanallarni olish"""
        result = await session.execute(
            select(MandatoryChannel).order_by(MandatoryChannel.id)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_channel_by_id(cls, session: AsyncSession, channel_id: int) -> Optional[MandatoryChannel]:
        """ID bo'yicha kanalni topish"""
        result = await session.execute(
            select(MandatoryChannel).where(MandatoryChannel.id == channel_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def add_channel(
        cls,
        session: AsyncSession,
        channel_id: str,
        title: str,
        invite_link: str,
        username: Optional[str] = None,
    ) -> MandatoryChannel:
        """Yangi majburiy kanal qo'shish"""
        # Mavjudligini tekshirish
        result = await session.execute(
            select(MandatoryChannel).where(MandatoryChannel.channel_id == channel_id)
        )
        channel = result.scalar_one_or_none()
        if channel:
            channel.title = title
            channel.invite_link = invite_link
            channel.username = username
            channel.is_active = True
            await session.commit()
            await session.refresh(channel)
            return channel

        channel = MandatoryChannel(
            channel_id=channel_id,
            title=title,
            username=username,
            invite_link=invite_link,
            is_active=True,
        )
        session.add(channel)
        await session.commit()
        await session.refresh(channel)
        return channel

    @classmethod
    async def delete_channel(cls, session: AsyncSession, channel_id: int) -> bool:
        """Kanalni o'chirish"""
        channel = await cls.get_channel_by_id(session, channel_id)
        if not channel:
            return False
        await session.delete(channel)
        await session.commit()
        return True

    @classmethod
    async def toggle_channel_status(cls, session: AsyncSession, channel_id: int) -> Optional[MandatoryChannel]:
        """Kanal holatini faol / nofaol qilish"""
        channel = await cls.get_channel_by_id(session, channel_id)
        if not channel:
            return None
        channel.is_active = not channel.is_active
        await session.commit()
        await session.refresh(channel)
        return channel

    @classmethod
    async def init_default_channel(cls, session: AsyncSession) -> None:
        """Boshlang'ich default kanalni kiritish (@ibn_sino_maktabi)"""
        channels = await cls.get_all_channels(session)
        if not channels:
            default_channel = MandatoryChannel(
                channel_id="@ibn_sino_maktabi",
                title="Ibn Sino Maktabi",
                username="@ibn_sino_maktabi",
                invite_link="https://t.me/ibn_sino_maktabi",
                is_active=True,
            )
            session.add(default_channel)
            await session.commit()
            logger.info("Boshlang'ich majburiy kanal (@ibn_sino_maktabi) muvaffaqiyatli qo'shildi.")

    @classmethod
    async def check_user_subscription(
        cls,
        bot: Bot,
        session: AsyncSession,
        user_id: int,
    ) -> Tuple[bool, List[MandatoryChannel]]:
        """
        Foydalanuvchining barcha faol majburiy kanallarga a'zoligini tekshirish.
        Qaytaradi: (barchasiga a'zomi?, a'zo bo'linmagan kanallar ro'yxati)
        """
        active_channels = await cls.get_active_channels(session)
        if not active_channels:
            return True, []

        unsubscribed: List[MandatoryChannel] = []

        allowed_statuses = {
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.RESTRICTED,
        }

        for channel in active_channels:
            # chat_id integer yoki @username bo'lishi mumkin
            chat_target: int | str = channel.channel_id
            if str(chat_target).startswith("-") and chat_target[1:].isdigit():
                chat_target = int(chat_target)

            try:
                member = await bot.get_chat_member(chat_id=chat_target, user_id=user_id)
                if member.status not in allowed_statuses:
                    unsubscribed.append(channel)
            except TelegramBadRequest as e:
                err_text = str(e).lower()
                # Agar user topilmasa yoki chatda a'zo bo'lmasa -> obuna bo'lmagan
                if "user not found" in err_text or "participant" in err_text:
                    unsubscribed.append(channel)
                elif "chat not found" in err_text or "not enough rights" in err_text:
                    # Bot bu kanalda admin emas yoki kanal xususiy bo'lib bot a'zo emas
                    logger.warning(
                        f"Majburiy kanal tekshiruvi: Bot {channel.title} ({channel.channel_id}) da tekshirish huquqiga ega emas: {e}"
                    )
                    # Foydalanuvchini bloklamaymiz, lekin kanalni belgilab qo'yish mumkin
                else:
                    unsubscribed.append(channel)
            except TelegramAPIError as e:
                logger.warning(f"Kanal a'zoligini tekshirishda Telegram xatoligi: {e}")
                # Kutilmagan tarmoq yoki API xatoligida foydalanuvchini bloklamaslik tavsiya etiladi

        is_all_subscribed = len(unsubscribed) == 0
        return is_all_subscribed, unsubscribed
