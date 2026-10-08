from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin_kb import get_sessions_select_list_kb
from bot.middlewares.admin_check import IsAdminFilter
from bot.services.excel_service import ExcelService
from bot.services.report_service import ReportService
from bot.services.session_service import SessionService

admin_reports_router = Router(name="admin_reports")
admin_reports_router.message.filter(IsAdminFilter())
admin_reports_router.callback_query.filter(IsAdminFilter())


@admin_reports_router.message(F.text == "📊 Hisobot")
async def show_reports_session_select(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Hisobot ko'rish uchun seans tanlash"""
    await state.clear()
    sessions = await SessionService.get_all_active_sessions(session)
    if not sessions:
        await message.answer("⚠️ Hozircha birorta ham seans mavjud emas.")
        return

    await message.answer(
        "📊 <b>Hisobot ko'rish:</b>\n\nQaysi imtihon seansi hisobotini ko'rmoqchisiz? Tanlang:",
        reply_markup=get_sessions_select_list_kb(sessions, prefix="adm_rep_view"),
        parse_mode="HTML",
    )


@admin_reports_router.callback_query(F.data.startswith("adm_rep_view:"))
async def view_session_report(callback: CallbackQuery, session: AsyncSession) -> None:
    """Seans hisobotini ko'rsatish"""
    await callback.answer()
    sess_id = int(callback.data.split(":")[1])
    report = await ReportService.get_session_report(session, sess_id)
    if not report:
        if callback.message:
            await callback.message.edit_text("⚠️ Hisobot ma'lumotlari topilmadi.")
        return

    rooms_text = ""
    for r in report.rooms:
        icon = "🔴" if r.free == 0 else "🟢"
        rooms_text += (
            f"\n• 🚪 <b>{r.room_name}</b>: {r.registered}/{r.capacity} ta ({r.fill_percent}%) "
            f"{icon} (Bo'sh: {r.free} ta)"
        )

    text = (
        f"📊 <b>IMTIHON HISOBOTI</b>\n\n"
        f"📚 Fan: <b>{report.subject_name}</b>\n"
        f"📍 Bino: {report.location_name}\n"
        f"📅 Sana: {report.exam_date} | 🕑 Vaqt: {report.start_time}\n"
        f"⚙️ Holati: <b>{report.status.upper()}</b>\n\n"
        f"👥 <b>Umumiy ko'rsatkichlar:</b>\n"
        f"• Jami o'rinlar: {report.total_capacity} ta\n"
        f"• Ro'yxatdan o'tganlar: <b>{report.total_registered} ta</b>\n"
        f"• Qolgan bo'sh joylar: <b>{report.total_free} ta</b>\n\n"
        f"🚪 <b>Xonalar bo'yicha taqsimot:</b>{rooms_text}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 Excel yuklab olish", callback_data=f"adm_xl_get:{report.session_id}")],
            [
                InlineKeyboardButton(text="⬅️ Seanslar", callback_data="adm_sess_list"),
                InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="adm_main"),
            ],
        ]
    )

    if callback.message:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


# ------------------- EXCEL YUKLAB OLISH -------------------
@admin_reports_router.message(F.text == "📥 Excel yuklab olish")
async def show_excel_session_select(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Excel yuklab olish uchun seans tanlash"""
    await state.clear()
    sessions = await SessionService.get_all_active_sessions(session)
    if not sessions:
        await message.answer("⚠️ Hozircha birorta ham seans mavjud emas.")
        return

    await message.answer(
        "📥 <b>Davomat varaqasini yuklab olish (Excel):</b>\n\nKerakli imtihon seansini tanlang:",
        reply_markup=get_sessions_select_list_kb(sessions, prefix="adm_xl_get"),
        parse_mode="HTML",
    )


@admin_reports_router.callback_query(F.data.startswith("adm_xl_get:"))
async def download_excel_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """Excel faylini generatsiya qilish va foydalanuvchiga yuborish"""
    await callback.answer("Excel varaqasi shakllantirilmoqda...", show_alert=False)
    sess_id = int(callback.data.split(":")[1])

    sess = await SessionService.get_session_by_id(session, sess_id)
    if not sess:
        if callback.message:
            await callback.message.answer("⚠️ Seans topilmadi.")
        return

    excel_file = await ExcelService.generate_attendance_sheet(session, sess_id)
    filename = f"Davomat_{sess.subject.name}_{sess.exam_date.strftime('%d.%m.%Y')}.xlsx"
    doc = BufferedInputFile(excel_file.getvalue(), filename=filename)

    if callback.message:
        await callback.message.answer_document(
            document=doc,
            caption=(
                f"📥 <b>Imtihon davomat varaqasi</b>\n\n"
                f"📚 Fan: {sess.subject.name}\n"
                f"📅 Sana: {sess.exam_date.strftime('%d.%m.%Y')} {sess.start_time.strftime('%H:%M')}\n"
                f"📍 Manzil: {sess.location.name}"
            ),
            parse_mode="HTML",
        )
