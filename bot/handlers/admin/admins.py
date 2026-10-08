from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin_kb import get_admins_manage_kb
from bot.middlewares.admin_check import IsAdminFilter
from bot.services.admin_service import AdminService
from bot.states.admin_states import AdminManagementStates

admin_management_router = Router(name="admin_management")
admin_management_router.message.filter(IsAdminFilter())
admin_management_router.callback_query.filter(IsAdminFilter())


@admin_management_router.message(F.text == "👥 Adminlar")
async def show_admins_menu(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Adminlar ro'yxati"""
    await state.clear()
    admins = await AdminService.get_all_admins(session)
    await message.answer(
        "👥 <b>Adminlar boshqaruvi:</b>\n\nQuyida tizimdagi qo'shimcha adminlar ro'yxati keltirilgan:",
        reply_markup=get_admins_manage_kb(admins),
        parse_mode="HTML",
    )


@admin_management_router.callback_query(F.data == "adm_usr_list")
async def show_admins_cb(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Adminlar ro'yxatiga qaytish"""
    await state.clear()
    await callback.answer()
    admins = await AdminService.get_all_admins(session)
    if callback.message:
        await callback.message.edit_text(
            "👥 <b>Adminlar boshqaruvi:</b>\n\nAdminlar ro'yxati:",
            reply_markup=get_admins_manage_kb(admins),
            parse_mode="HTML",
        )


@admin_management_router.callback_query(F.data == "adm_usr_add")
async def start_add_admin(callback: CallbackQuery, state: FSMContext) -> None:
    """Yangi admin qo'shish"""
    await callback.answer()
    await state.set_state(AdminManagementStates.waiting_telegram_id)
    if callback.message:
        await callback.message.edit_text(
            "👥 <b>Yangi admin qo'shish</b>\n\nQo'shmoqchi bo'lgan foydalanuvchining <b>Telegram ID</b> raqamini kiriting:\n<i>(Masalan: 123456789)</i>",
            parse_mode="HTML",
        )


@admin_management_router.message(AdminManagementStates.waiting_telegram_id)
async def process_admin_tg_id(message: Message, state: FSMContext) -> None:
    """Telegram ID tekshirildi"""
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("⚠️ Telegram ID faqat raqamlardan iborat bo'lishi kerak. Qaytadan kiriting:")
        return

    tg_id = int(text)
    await state.update_data(tg_id=tg_id)
    await state.set_state(AdminManagementStates.waiting_full_name)
    await message.answer(
        f"🆔 ID: <code>{tg_id}</code>\n\nEndi adminning ism-familiyasini kiriting:\n<i>(Masalan: Alisher Qodirov)</i>",
        parse_mode="HTML",
    )


@admin_management_router.message(AdminManagementStates.waiting_full_name)
async def process_admin_name(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Admin nomi kiritildi va saqlandi"""
    full_name = (message.text or "").strip()
    data = await state.get_data()
    tg_id = data.get("tg_id")
    await state.clear()

    admin = await AdminService.add_admin(session, telegram_id=tg_id, full_name=full_name)
    admins = await AdminService.get_all_admins(session)

    await message.answer(
        f"🎉 <b>Yangi admin muvaffaqiyatli qo'shildi!</b>\n\n👤 Ism: <b>{admin.full_name}</b>\n🆔 Telegram ID: <code>{admin.telegram_id}</code>",
        reply_markup=get_admins_manage_kb(admins),
        parse_mode="HTML",
    )


@admin_management_router.callback_query(F.data.startswith("adm_usr_del:"))
async def delete_admin_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """Adminni o'chirish"""
    tg_id = int(callback.data.split(":")[1])
    deleted = await AdminService.remove_admin(session, tg_id)
    await callback.answer("Admin o'chirildi!" if deleted else "Topilmadi", show_alert=True)

    admins = await AdminService.get_all_admins(session)
    if callback.message:
        await callback.message.edit_text(
            "👥 <b>Adminlar boshqaruvi:</b>\n\nAdmin o'chirildi. Yangilangan ro'yxat:",
            reply_markup=get_admins_manage_kb(admins),
            parse_mode="HTML",
        )
