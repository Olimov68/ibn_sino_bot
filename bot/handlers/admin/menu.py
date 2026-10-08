from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin_kb import get_admin_main_menu_kb
from bot.middlewares.admin_check import IsAdminFilter

admin_menu_router = Router(name="admin_menu")
admin_menu_router.message.filter(IsAdminFilter())
admin_menu_router.callback_query.filter(IsAdminFilter())


@admin_menu_router.message(F.text == "🏠 Asosiy menyu")
async def handle_admin_home_message(message: Message, state: FSMContext) -> None:
    """Admin asosiy menyusiga qaytish"""
    await state.clear()
    await message.answer(
        "🛠 <b>Boshqaruv paneli (Admin)</b>\n\nQuyidagi bo'limlardan birini tanlang:",
        reply_markup=get_admin_main_menu_kb(),
        parse_mode="HTML",
    )


@admin_menu_router.callback_query(F.data == "adm_main")
async def handle_admin_home_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Inline tugma orqali admin paneliga qaytish"""
    await state.clear()
    await callback.answer()
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            "🛠 <b>Boshqaruv paneli (Admin)</b>\n\nQuyidagi bo'limlardan birini tanlang:",
            reply_markup=get_admin_main_menu_kb(),
            parse_mode="HTML",
        )

