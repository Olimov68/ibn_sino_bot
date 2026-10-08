from typing import Any, Awaitable, Callable, Dict, Union
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.admin_service import AdminService


class IsAdminFilter(Filter):
    """Foydalanuvchi admin ekanligini tekshiruvchi aiogram 3 filtri"""

    async def __call__(
        self,
        event: Union[Message, CallbackQuery],
        session: AsyncSession,
    ) -> bool:
        user = getattr(event, "from_user", None)
        if not user:
            return False
        return await AdminService.is_admin(session, user.id)
