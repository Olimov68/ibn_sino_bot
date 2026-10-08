from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def get_cancel_reply_kb() -> ReplyKeyboardMarkup:
    """Bekor qilish va orqaga qaytish reply klaviaturasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Asosiy menyu")],
        ],
        resize_keyboard=True,
    )


def get_back_inline_kb(callback_data: str = "admin_main") -> InlineKeyboardMarkup:
    """Orqaga va Asosiy menyu inline tugmalari"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Orqaga", callback_data=callback_data),
                InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="admin_main"),
            ]
        ]
    )
