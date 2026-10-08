from unittest.mock import AsyncMock, MagicMock
import pytest
from aiogram.enums import ChatMemberStatus
from bot.services.channel_service import ChannelService


@pytest.mark.asyncio
async def test_init_default_channel(db_session):
    """Boshlang'ich default kanal qo'shilishini tekshirish"""
    await ChannelService.init_default_channel(db_session)
    channels = await ChannelService.get_all_channels(db_session)
    assert len(channels) == 1
    assert channels[0].channel_id == "@ibn_sino_maktabi"
    assert channels[0].is_active is True


@pytest.mark.asyncio
async def test_channel_crud_operations(db_session):
    """Kanal qo'shish, statusini o'zgartirish va o'chirishni tekshirish"""
    ch = await ChannelService.add_channel(
        session=db_session,
        channel_id="@test_channel",
        title="Test Kanal",
        invite_link="https://t.me/test_channel",
        username="@test_channel",
    )
    assert ch.id is not None
    assert ch.title == "Test Kanal"

    # Statusni o'zgartirish (faol -> nofaol)
    updated = await ChannelService.toggle_channel_status(db_session, ch.id)
    assert updated.is_active is False

    active_channels = await ChannelService.get_active_channels(db_session)
    assert len(active_channels) == 0

    # Qayta faollashtirish
    updated = await ChannelService.toggle_channel_status(db_session, ch.id)
    assert updated.is_active is True

    # O'chirish
    deleted = await ChannelService.delete_channel(db_session, ch.id)
    assert deleted is True

    channels = await ChannelService.get_all_channels(db_session)
    assert len(channels) == 0


@pytest.mark.asyncio
async def test_check_user_subscription(db_session):
    """Kanal a'zoligini tekshirish mantig'ini test qilish"""
    await ChannelService.add_channel(
        session=db_session,
        channel_id="@channel_one",
        title="Kanal 1",
        invite_link="https://t.me/channel_one",
    )

    mock_bot = MagicMock()
    mock_member = MagicMock()

    # 1. Obuna bo'lgan holat (member)
    mock_member.status = ChatMemberStatus.MEMBER
    mock_bot.get_chat_member = AsyncMock(return_value=mock_member)

    is_sub, unsub = await ChannelService.check_user_subscription(mock_bot, db_session, 12345678)
    assert is_sub is True
    assert len(unsub) == 0

    # 2. Chiqib ketgan holat (left)
    mock_member.status = ChatMemberStatus.LEFT
    is_sub, unsub = await ChannelService.check_user_subscription(mock_bot, db_session, 12345678)
    assert is_sub is False
    assert len(unsub) == 1
    assert unsub[0].channel_id == "@channel_one"
