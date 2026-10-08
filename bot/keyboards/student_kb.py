import datetime
from typing import Any, Dict, List
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.db.models.registration import Registration
from bot.db.models.subject import Subject


def get_student_main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """O'quvchi asosiy menyusi (Reply klaviatura)"""
    keyboard = [
        [KeyboardButton(text="📝 Imtihonga yozilish")],
        [KeyboardButton(text="📋 Mening ro'yxatlarim"), KeyboardButton(text="👤 Profilim")],
        [KeyboardButton(text="ℹ️ Markaz haqida / Aloqa")],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="🛠 Admin paneliga qaytish")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def get_phone_request_kb() -> ReplyKeyboardMarkup:
    """Telefon raqamni bitta bosishda yuborish tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_grades_kb() -> InlineKeyboardMarkup:
    """Sinfni tanlash tugmalari (5-11 sinflar)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="5-sinf", callback_data="grade:5"),
                InlineKeyboardButton(text="6-sinf", callback_data="grade:6"),
                InlineKeyboardButton(text="7-sinf", callback_data="grade:7"),
                InlineKeyboardButton(text="8-sinf", callback_data="grade:8"),
            ],
            [
                InlineKeyboardButton(text="9-sinf", callback_data="grade:9"),
                InlineKeyboardButton(text="10-sinf", callback_data="grade:10"),
                InlineKeyboardButton(text="11-sinf", callback_data="grade:11"),
            ],
        ]
    )


def get_student_subjects_kb(subjects: List[Subject]) -> InlineKeyboardMarkup:
    """Imtihon topshirish uchun fanlar ro'yxati"""
    kb: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []
    for idx, sub in enumerate(subjects):
        row.append(InlineKeyboardButton(text=f"📚 {sub.name}", callback_data=f"stu_sub:{sub.id}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)

    kb.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_student_dates_kb(dates: List[datetime.date]) -> InlineKeyboardMarkup:
    """Fan bo'yicha mavjud sanalar ro'yxati"""
    kb: List[List[InlineKeyboardButton]] = []
    for d in dates:
        d_str = d.strftime("%d.%m.%Y")
        kb.append([InlineKeyboardButton(text=f"📅 {d_str}", callback_data=f"stu_date:{d_str}")])

    kb.append([
        InlineKeyboardButton(text="⬅️ Fanlar", callback_data="stu_book_start"),
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_student_times_kb(session_items: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Mavjud vaqtlar va bo'sh o'rinlar soni"""
    kb: List[List[InlineKeyboardButton]] = []
    for item in session_items:
        sess = item["session"]
        rem = item["remaining"]
        time_str = sess.start_time.strftime("%H:%M")
        loc_name = sess.location.name
        btn_text = f"🕑 {time_str} | {loc_name} (Bo'sh: {rem} ta)"
        kb.append([InlineKeyboardButton(text=btn_text, callback_data=f"stu_sess:{sess.id}")])

    kb.append([
        InlineKeyboardButton(text="⬅️ Sanalar", callback_data="stu_back_dates"),
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_my_registrations_kb(registrations: List[Registration]) -> InlineKeyboardMarkup:
    """O'quvchining yozilgan imtihonlari va bekor qilish tugmalari"""
    kb: List[List[InlineKeyboardButton]] = []
    for reg in registrations:
        date_str = reg.session.exam_date.strftime("%d.%m")
        time_str = reg.session.start_time.strftime("%H:%M")
        btn_text = f"❌ Bekor qilish: {reg.session.subject.name} ({date_str} {time_str})"
        kb.append([InlineKeyboardButton(text=btn_text, callback_data=f"stu_cancel:{reg.id}")])

    kb.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_profile_edit_kb() -> InlineKeyboardMarkup:
    """Profilni tahrirlash tugmalari"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Ismni o'zgartirish", callback_data="stu_prof_edit_name")],
            [InlineKeyboardButton(text="📱 Telefonni o'zgartirish", callback_data="stu_prof_edit_phone")],
            [InlineKeyboardButton(text="🎓 Sinfni o'zgartirish", callback_data="stu_prof_edit_grade")],
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home")],
        ]
    )
