from typing import List
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from bot.db.models.admin import Admin
from bot.db.models.location import Location
from bot.db.models.room import Room
from bot.db.models.session import ExamSession
from bot.db.models.subject import Subject
from bot.db.models.channel import MandatoryChannel


def get_admin_main_menu_kb() -> ReplyKeyboardMarkup:
    """Admin asosiy paneli uchun Reply klaviatura"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Manzillar"), KeyboardButton(text="🚪 Xonalar")],
            [KeyboardButton(text="📚 Fanlar"), KeyboardButton(text="🗓 Imtihon seanslari")],
            [KeyboardButton(text="📊 Hisobot"), KeyboardButton(text="📥 Excel yuklab olish")],
            [KeyboardButton(text="📢 Xabar yuborish"), KeyboardButton(text="👥 Adminlar")],
            [KeyboardButton(text="📢 Majburiy obuna"), KeyboardButton(text="🔙 O'quvchi rejimiga o'tish")],
        ],
        resize_keyboard=True,
    )


# ------------------- MANZILLAR -------------------
def get_locations_manage_kb(locations: List[Location]) -> InlineKeyboardMarkup:
    """Manzillar boshqaruvi klaviaturasi"""
    kb: List[List[InlineKeyboardButton]] = []
    for loc in locations:
        kb.append([InlineKeyboardButton(text=f"📍 {loc.name}", callback_data=f"adm_loc_view:{loc.id}")])
    kb.append([InlineKeyboardButton(text="➕ Manzil qo'shish", callback_data="adm_loc_add")])
    kb.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_location_item_kb(location_id: int) -> InlineKeyboardMarkup:
    """Bitta manzil uchun amallar"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Manzilni o'chirish", callback_data=f"adm_loc_del:{location_id}")],
            [
                InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_loc_list"),
                InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main"),
            ],
        ]
    )


# ------------------- XONALAR -------------------
def get_locations_for_rooms_kb(locations: List[Location]) -> InlineKeyboardMarkup:
    """Xonalarni ko'rish uchun manzil tanlash"""
    kb: List[List[InlineKeyboardButton]] = []
    for loc in locations:
        kb.append([InlineKeyboardButton(text=f"🏢 {loc.name}", callback_data=f"adm_room_loc:{loc.id}")])
    kb.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_rooms_manage_kb(location_id: int, rooms: List[Room]) -> InlineKeyboardMarkup:
    """Manzildagi xonalar boshqaruvi"""
    kb: List[List[InlineKeyboardButton]] = []
    for room in rooms:
        kb.append([
            InlineKeyboardButton(
                text=f"🚪 {room.name} ({room.capacity} ta joy, tartib: {room.sort_order})",
                callback_data=f"adm_room_view:{room.id}",
            )
        ])
    kb.append([InlineKeyboardButton(text="➕ Xona qo'shish", callback_data=f"adm_room_add:{location_id}")])
    kb.append([
        InlineKeyboardButton(text="⬅️ Manzillar", callback_data="adm_rooms_menu"),
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_room_item_kb(room_id: int, location_id: int) -> InlineKeyboardMarkup:
    """Bitta xona uchun amallar"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"adm_room_edit:{room_id}"),
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_room_del:{room_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"adm_room_loc:{location_id}"),
                InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main"),
            ],
        ]
    )


# ------------------- FANLAR -------------------
def get_subjects_manage_kb(subjects: List[Subject]) -> InlineKeyboardMarkup:
    """Fanlar boshqaruvi"""
    kb: List[List[InlineKeyboardButton]] = []
    for sub in subjects:
        kb.append([
            InlineKeyboardButton(text=f"📚 {sub.name}", callback_data=f"adm_sub_view:{sub.id}"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_sub_del:{sub.id}"),
        ])
    kb.append([InlineKeyboardButton(text="➕ Fan qo'shish", callback_data="adm_sub_add")])
    kb.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ------------------- IMTIHON SEANSLARI -------------------
def get_sessions_manage_kb(sessions: List[ExamSession]) -> InlineKeyboardMarkup:
    """Seanslar boshqaruvi ro'yxati"""
    kb: List[List[InlineKeyboardButton]] = []
    kb.append([InlineKeyboardButton(text="➕ Yangi seans yaratish", callback_data="adm_sess_add")])
    for s in sessions:
        date_str = s.exam_date.strftime("%d.%m")
        time_str = s.start_time.strftime("%H:%M")
        status_icon = "🟢" if s.status == "open" else ("🟡" if s.status == "full" else "🔴")
        kb.append([
            InlineKeyboardButton(
                text=f"{status_icon} {s.subject.name} | {date_str} {time_str}",
                callback_data=f"adm_sess_view:{s.id}",
            )
        ])
    kb.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_session_item_kb(session_id: int, is_open: bool) -> InlineKeyboardMarkup:
    """Bitta seans uchun amallar"""
    kb: List[List[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="📊 Hisobot", callback_data=f"adm_rep_view:{session_id}"),
            InlineKeyboardButton(text="📥 Excel yuklab olish", callback_data=f"adm_xl_get:{session_id}"),
        ],
        [InlineKeyboardButton(text="📢 Xabar yuborish", callback_data=f"adm_bc_start:{session_id}")],
    ]
    if is_open:
        kb.append([InlineKeyboardButton(text="🔒 Seansni yopish", callback_data=f"adm_sess_close:{session_id}")])
    kb.append([
        InlineKeyboardButton(text="⬅️ Seanslar", callback_data="adm_sess_list"),
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ------------------- SELECTIONS FOR CREATING SESSIONS -------------------
def get_subjects_selection_kb(subjects: List[Subject]) -> InlineKeyboardMarkup:
    """Seans yaratishda fan tanlash"""
    kb: List[List[InlineKeyboardButton]] = []
    for sub in subjects:
        kb.append([InlineKeyboardButton(text=f"📚 {sub.name}", callback_data=f"adm_sel_sub:{sub.id}")])
    kb.append([InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="adm_sess_list")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_locations_selection_kb(locations: List[Location]) -> InlineKeyboardMarkup:
    """Seans yaratishda manzil tanlash"""
    kb: List[List[InlineKeyboardButton]] = []
    for loc in locations:
        kb.append([InlineKeyboardButton(text=f"📍 {loc.name}", callback_data=f"adm_sel_loc:{loc.id}")])
    kb.append([InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="adm_sess_list")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ------------------- HISOBOT & EXCEL & BROADCAST LISTS -------------------
def get_sessions_select_list_kb(sessions: List[ExamSession], prefix: str) -> InlineKeyboardMarkup:
    """Hisobot, Excel yoki Xabar yuborish uchun seans tanlash ro'yxati"""
    kb: List[List[InlineKeyboardButton]] = []
    for s in sessions:
        date_str = s.exam_date.strftime("%d.%m")
        time_str = s.start_time.strftime("%H:%M")
        status_icon = "🟢" if s.status == "open" else ("🟡" if s.status == "full" else "🔴")
        kb.append([
            InlineKeyboardButton(
                text=f"{status_icon} {s.subject.name} | {date_str} {time_str}",
                callback_data=f"{prefix}:{s.id}",
            )
        ])
    kb.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ------------------- ADMINLAR BOSHQARUVI -------------------
def get_admins_manage_kb(admins: List[Admin]) -> InlineKeyboardMarkup:
    """Adminlar ro'yxati va boshqaruvi"""
    kb: List[List[InlineKeyboardButton]] = []
    for adm in admins:
        name_str = f"👤 {adm.full_name or 'Admin'} ({adm.telegram_id})"
        kb.append([
            InlineKeyboardButton(text=name_str, callback_data=f"adm_usr_view:{adm.telegram_id}"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_usr_del:{adm.telegram_id}"),
        ])
    kb.append([InlineKeyboardButton(text="➕ Yangi admin qo'shish", callback_data="adm_usr_add")])
    kb.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ------------------- MAJBURIY OBUNA BOSHQARUVI -------------------
def get_channels_manage_kb(channels: List[MandatoryChannel]) -> InlineKeyboardMarkup:
    """Majburiy kanallar ro'yxati va boshqaruvi"""
    kb: List[List[InlineKeyboardButton]] = []
    for ch in channels:
        status_icon = "🟢" if ch.is_active else "🔴"
        title_str = f"{status_icon} {ch.title}"
        kb.append([
            InlineKeyboardButton(text=title_str, callback_data=f"adm_ch_view:{ch.id}"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_ch_del:{ch.id}"),
        ])
    kb.append([InlineKeyboardButton(text="➕ Yangi kanal qo'shish", callback_data="adm_ch_add")])
    kb.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_channel_item_kb(channel: MandatoryChannel) -> InlineKeyboardMarkup:
    """Bitta kanal uchun amallar"""
    status_text = "🔴 Nofaol qilish" if channel.is_active else "🟢 Faollashtirish"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=status_text, callback_data=f"adm_ch_toggle:{channel.id}")],
            [InlineKeyboardButton(text="🗑 Kanalni o'chirish", callback_data=f"adm_ch_del:{channel.id}")],
            [
                InlineKeyboardButton(text="⬅️ Kanallar ro'yxati", callback_data="adm_ch_list"),
                InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main"),
            ],
        ]
    )


def get_cancel_channel_add_kb() -> InlineKeyboardMarkup:
    """Kanal qo'shishni bekor qilish"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm_ch_list")]
        ]
    )

