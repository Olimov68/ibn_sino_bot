from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin_kb import (
    get_locations_for_rooms_kb,
    get_room_item_kb,
    get_rooms_manage_kb,
)
from bot.middlewares.admin_check import IsAdminFilter
from bot.services.location_service import LocationService
from bot.services.room_service import RoomService
from bot.states.admin_states import RoomStates

admin_rooms_router = Router(name="admin_rooms")
admin_rooms_router.message.filter(IsAdminFilter())
admin_rooms_router.callback_query.filter(IsAdminFilter())


@admin_rooms_router.message(F.text == "🚪 Xonalar")
async def show_rooms_location_menu(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Xonalar bo'limi: avval manzilni tanlash"""
    await state.clear()
    locations = await LocationService.get_locations(session)
    if not locations:
        await message.answer("⚠️ Hozircha hech qanday manzil mavjud emas. Avval 📍 Manzillar bo'limidan manzil qo'shing.")
        return

    await message.answer(
        "🚪 <b>Xonalar boshqaruvi:</b>\n\nXonalarini ko'rish yoki yangi xona qo'shish uchun bino/manzilni tanlang:",
        reply_markup=get_locations_for_rooms_kb(locations),
        parse_mode="HTML",
    )


@admin_rooms_router.callback_query(F.data == "adm_rooms_menu")
async def show_rooms_location_menu_cb(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Xonalar uchun manzil tanlash menyusiga qaytish"""
    await state.clear()
    await callback.answer()
    locations = await LocationService.get_locations(session)
    if callback.message:
        await callback.message.edit_text(
            "🚪 <b>Xonalar boshqaruvi:</b>\n\nBino/manzilni tanlang:",
            reply_markup=get_locations_for_rooms_kb(locations),
            parse_mode="HTML",
        )


@admin_rooms_router.callback_query(F.data.startswith("adm_room_loc:"))
async def show_rooms_in_location(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Tanlangan manzildagi xonalar ro'yxati"""
    await state.clear()
    await callback.answer()
    loc_id = int(callback.data.split(":")[1])
    location = await LocationService.get_location_by_id(session, loc_id)
    if not location:
        if callback.message:
            await callback.message.edit_text("⚠️ Manzil topilmadi.")
        return

    rooms = await RoomService.get_rooms_by_location(session, loc_id)
    text = (
        f"🏢 <b>Bino: {location.name}</b>\n\n"
        f"Ushbu manzildagi xonalar soni: {len(rooms)} ta\n"
        f"Kerakli xonani tanlang yoki yangisini qo'shing:"
    )
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_rooms_manage_kb(loc_id, rooms),
            parse_mode="HTML",
        )


@admin_rooms_router.callback_query(F.data.startswith("adm_room_add:"))
async def start_add_room(callback: CallbackQuery, state: FSMContext) -> None:
    """Xona qo'shishni boshlash"""
    await callback.answer()
    loc_id = int(callback.data.split(":")[1])
    await state.update_data(location_id=loc_id)
    await state.set_state(RoomStates.waiting_name)
    if callback.message:
        await callback.message.edit_text(
            "🚪 <b>Yangi xona qo'shish</b>\n\nXona nomini yoki raqamini kiriting:\n<i>(Masalan: 101-xona yoki Kimyo laboratoriyasi)</i>",
            parse_mode="HTML",
        )


@admin_rooms_router.message(RoomStates.waiting_name)
async def process_room_name(message: Message, state: FSMContext) -> None:
    """Xona nomi kiritildi"""
    name = (message.text or "").strip()
    if not name:
        await message.answer("⚠️ Xona nomini to'g'ri kiriting:")
        return

    await state.update_data(name=name)
    await state.set_state(RoomStates.waiting_capacity)
    await message.answer(
        f"🚪 Xona nomi: <b>{name}</b>\n\nEndi ushbu xonadagi <b>stollar (o'rinlar) sonini</b> kiriting:\n<i>(Faqat musbat butun son, masalan: 20)</i>",
        parse_mode="HTML",
    )


@admin_rooms_router.message(RoomStates.waiting_capacity)
async def process_room_capacity(message: Message, state: FSMContext) -> None:
    """Sig'im kiritildi"""
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("⚠️ Stollar soni musbat butun son bo'lishi kerak (masalan: 15). Qaytadan kiriting:")
        return

    capacity = int(text)
    await state.update_data(capacity=capacity)
    await state.set_state(RoomStates.waiting_sort_order)
    await message.answer(
        f"🪑 Stollar soni: <b>{capacity}</b> ta\n\n"
        f"Endi to'ldirish tartibi raqamini (sort_order) kiriting:\n"
        f"<i>(Masalan: 1 — birinchi bo'lib shu xona to'ldiriladi; 2 — keyingisi)</i>",
        parse_mode="HTML",
    )


@admin_rooms_router.message(RoomStates.waiting_sort_order)
async def process_room_sort_order(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Tartib raqami kiritildi va saqlandi"""
    text = (message.text or "").strip()
    sort_order = int(text) if text.isdigit() else 0

    data = await state.get_data()
    loc_id = data.get("location_id")
    name = data.get("name")
    capacity = data.get("capacity")
    await state.clear()

    room = await RoomService.create_room(
        session,
        location_id=loc_id,
        name=name,
        capacity=capacity,
        sort_order=sort_order,
    )
    rooms = await RoomService.get_rooms_by_location(session, loc_id)

    await message.answer(
        f"🎉 <b>Xona muvaffaqiyatli yaratildi!</b>\n\n"
        f"🚪 Nomi: <b>{room.name}</b>\n"
        f"🪑 Sig'imi: {room.capacity} ta stol\n"
        f"🔢 To'ldirish navbati (tartib): {room.sort_order}",
        reply_markup=get_rooms_manage_kb(loc_id, rooms),
        parse_mode="HTML",
    )


@admin_rooms_router.callback_query(F.data.startswith("adm_room_view:"))
async def view_room_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    """Xona tafsilotlarini ko'rish"""
    await callback.answer()
    room_id = int(callback.data.split(":")[1])
    room = await RoomService.get_room_by_id(session, room_id)
    if not room:
        if callback.message:
            await callback.message.edit_text("⚠️ Xona topilmadi.")
        return

    text = (
        f"🚪 <b>Xona ma'lumotlari:</b>\n\n"
        f"🏷 Nomi: <b>{room.name}</b>\n"
        f"🪑 Sig'imi (stollar soni): {room.capacity} ta\n"
        f"🔢 To'ldirish navbati: {room.sort_order}\n"
        f"⚙️ Holati: {'Faol' if room.is_active else 'Nofaol'}"
    )
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_room_item_kb(room.id, room.location_id),
            parse_mode="HTML",
        )


@admin_rooms_router.callback_query(F.data.startswith("adm_room_del:"))
async def delete_room_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """Xonani o'chirish"""
    room_id = int(callback.data.split(":")[1])
    room = await RoomService.get_room_by_id(session, room_id)
    if not room:
        await callback.answer("Xona topilmadi", show_alert=True)
        return

    loc_id = room.location_id
    deleted = await RoomService.delete_room(session, room_id)
    if not deleted:
        await callback.answer(
            "⚠️ Ushbu xonada imtihonlar yoki ro'yxatdan o'tgan o'quvchilar mavjud bo'lgani sababli uni o'chirib bo'lmaydi!",
            show_alert=True,
        )
        return

    await callback.answer("Xona o'chirildi!", show_alert=True)

    rooms = await RoomService.get_rooms_by_location(session, loc_id)
    if callback.message:
        await callback.message.edit_text(
            "🚪 <b>Xonalar boshqaruvi:</b>\n\nXona o'chirildi. Yangilangan ro'yxat:",
            reply_markup=get_rooms_manage_kb(loc_id, rooms),
            parse_mode="HTML",
        )



@admin_rooms_router.callback_query(F.data.startswith("adm_room_edit:"))
async def edit_room_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Xona sig'imini tahrirlashni boshlash"""
    await callback.answer()
    room_id = int(callback.data.split(":")[1])
    await state.update_data(edit_room_id=room_id)
    await state.set_state(RoomStates.waiting_edit_capacity)
    if callback.message:
        await callback.message.edit_text(
            "✏️ <b>Xona sig'imini tahrirlash</b>\n\nYangi stollar sonini kiriting (masalan: 25):",
            parse_mode="HTML",
        )


@admin_rooms_router.message(RoomStates.waiting_edit_capacity)
async def process_edit_capacity(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Yangi sig'im kiritildi"""
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("⚠️ Iltimos, musbat son kiriting:")
        return

    new_cap = int(text)
    data = await state.get_data()
    room_id = data.get("edit_room_id")
    await state.clear()

    updated = await RoomService.update_room(session, room_id=room_id, capacity=new_cap)
    if not updated:
        await message.answer("⚠️ Xona topilmadi.")
        return

    rooms = await RoomService.get_rooms_by_location(session, updated.location_id)
    await message.answer(
        f"✅ <b>Xona sig'imi muvaffaqiyatli yangilandi!</b>\n\n🚪 Nomi: <b>{updated.name}</b>\n🪑 Yangi sig'imi: {updated.capacity} ta",
        reply_markup=get_rooms_manage_kb(updated.location_id, rooms),
        parse_mode="HTML",
    )
