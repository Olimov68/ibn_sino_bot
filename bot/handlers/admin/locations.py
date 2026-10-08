from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin_kb import get_location_item_kb, get_locations_manage_kb
from bot.middlewares.admin_check import IsAdminFilter
from bot.services.location_service import LocationService
from bot.states.admin_states import LocationStates

admin_locations_router = Router(name="admin_locations")
admin_locations_router.message.filter(IsAdminFilter())
admin_locations_router.callback_query.filter(IsAdminFilter())


@admin_locations_router.message(F.text == "📍 Manzillar")
async def show_locations_from_menu(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Admin menyusidan manzillar bo'limi"""
    await state.clear()
    locations = await LocationService.get_locations(session)
    await message.answer(
        "📍 <b>O'quv markazi manzillari:</b>\n\nQuyidagi manzillardan birini tanlang yoki yangisini qo'shing:",
        reply_markup=get_locations_manage_kb(locations),
        parse_mode="HTML",
    )


@admin_locations_router.callback_query(F.data == "adm_loc_list")
async def show_locations_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Manzillar ro'yxatiga qaytish"""
    await state.clear()
    await callback.answer()
    locations = await LocationService.get_locations(session)
    if callback.message:
        await callback.message.edit_text(
            "📍 <b>O'quv markazi manzillari:</b>\n\nQuyidagi manzillardan birini tanlang yoki yangisini qo'shing:",
            reply_markup=get_locations_manage_kb(locations),
            parse_mode="HTML",
        )


@admin_locations_router.callback_query(F.data == "adm_loc_add")
async def start_add_location(callback: CallbackQuery, state: FSMContext) -> None:
    """Yangi manzil qo'shishni boshlash"""
    await callback.answer()
    await state.set_state(LocationStates.waiting_name)
    if callback.message:
        await callback.message.edit_text(
            "📍 <b>Yangi manzil qo'shish</b>\n\nIltimos, filial yoki bino nomini kiriting:\n<i>(Masalan: Bosh bino yoki Chilonzor filiali)</i>",
            parse_mode="HTML",
        )


@admin_locations_router.message(LocationStates.waiting_name)
async def process_location_name(message: Message, state: FSMContext) -> None:
    """Manzil nomi kiritildi"""
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("⚠️ Manzil nomi juda qisqa. Qaytadan kiriting:")
        return

    await state.update_data(name=name)
    await state.set_state(LocationStates.waiting_address)
    await message.answer(
        f"✅ Nomi: <b>{name}</b>\n\nEndi ushbu filialning to'liq manzilini kiriting:\n<i>(Masalan: Toshkent sh., Navoiy ko'chasi, 15-uy)</i>",
        parse_mode="HTML",
    )


@admin_locations_router.message(LocationStates.waiting_address)
async def process_location_address(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Manzil manzili kiritildi va saqlandi"""
    address = (message.text or "").strip()
    data = await state.get_data()
    name = data.get("name")
    await state.clear()

    location = await LocationService.create_location(session, name=name, address=address)
    locations = await LocationService.get_locations(session)

    await message.answer(
        f"🎉 <b>Yangi manzil muvaffaqiyatli qo'shildi!</b>\n\n📍 Nomi: <b>{location.name}</b>\n📌 Manzil: {location.address}",
        reply_markup=get_locations_manage_kb(locations),
        parse_mode="HTML",
    )


@admin_locations_router.callback_query(F.data.startswith("adm_loc_view:"))
async def view_location_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    """Manzil tafsilotlarini ko'rish"""
    await callback.answer()
    loc_id = int(callback.data.split(":")[1])
    location = await LocationService.get_location_by_id(session, loc_id)
    if not location:
        if callback.message:
            await callback.message.edit_text("⚠️ Manzil topilmadi.")
        return

    rooms_count = len(location.rooms)
    text = (
        f"📍 <b>Manzil ma'lumotlari:</b>\n\n"
        f"🏷 Nomi: <b>{location.name}</b>\n"
        f"📌 Manzil: {location.address}\n"
        f"🚪 Xonalar soni: {rooms_count} ta\n"
    )
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_location_item_kb(location.id),
            parse_mode="HTML",
        )


@admin_locations_router.callback_query(F.data.startswith("adm_loc_del:"))
async def delete_location_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """Manzilni o'chirish"""
    loc_id = int(callback.data.split(":")[1])
    deleted = await LocationService.delete_location(session, loc_id)
    if not deleted:
        await callback.answer(
            "⚠️ Ushbu manzilga bog'langan xonalar yoki imtihonlar mavjud bo'lgani sababli uni o'chirib bo'lmaydi!",
            show_alert=True,
        )
        return

    await callback.answer("Manzil o'chirildi!", show_alert=True)

    locations = await LocationService.get_locations(session)
    if callback.message:
        await callback.message.edit_text(
            "📍 <b>O'quv markazi manzillari:</b>\n\nManzil o'chirildi. Ro'yxat:",
            reply_markup=get_locations_manage_kb(locations),
            parse_mode="HTML",
        )
