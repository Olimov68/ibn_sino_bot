from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

about_router = Router(name="student_about")


@about_router.message(F.text == "ℹ️ Markaz haqida / Aloqa")
async def show_about_center(message: Message) -> None:
    """O'quv markazi haqida ma'lumot va aloqa vositalari"""
    text = (
        "ℹ️ <b>IBN SINO MAKTABI — HAFTALIK MOCK IMTIHONLARI</b>\n\n"
        "Bizning o'quv markazimiz kimyo, biologiya, matematika, fizika, ingliz tili "
        "va boshqa fanlar bo'yicha DTM va xalqaro standartlardagi professional "
        "haftalik mock imtihonlarni tashkil etadi.\n\n"
        "🎯 <b>Afzalliklarimiz:</b>\n"
        "• Haqiqiy imtihon muhiti va tartibi;\n"
        "• Avtomatik xona va stollarga joylashtirish;\n"
        "• Tezkor va xolis natijalar tahlili;\n"
        "• Kuchli mutaxassislar tomonidan tuzilgan test savollari.\n\n"
        "📞 <b>Aloqa va ma'lumot:</b>\n"
        "• Call-markaz: +998 (99) 698-00-28\n"
        "• Telegram kanal: @ibn_sino_maktabi\n"
        "• Admin bilan bog'lanish: @ibn_sino_admin\n"
        "• Ish vaqti: Dushanba - Shanba (09:00 - 18:00)"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Rasmiy kanalimiz", url="https://t.me/ibn_sino_maktabi")],
            [InlineKeyboardButton(text="💬 Admin bilan bog'lanish", url="https://t.me/ibn_sino_admin")],
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="stu_home")],
        ]
    )

    await message.answer(text, reply_markup=kb, parse_mode="HTML")
