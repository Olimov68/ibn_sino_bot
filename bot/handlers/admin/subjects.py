from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin_kb import get_subjects_manage_kb
from bot.middlewares.admin_check import IsAdminFilter
from bot.services.subject_service import SubjectService
from bot.states.admin_states import SubjectStates

admin_subjects_router = Router(name="admin_subjects")
admin_subjects_router.message.filter(IsAdminFilter())
admin_subjects_router.callback_query.filter(IsAdminFilter())


@admin_subjects_router.message(F.text == "📚 Fanlar")
async def show_subjects_menu(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Fanlar bo'limi"""
    await state.clear()
    subjects = await SubjectService.get_subjects(session)
    await message.answer(
        "📚 <b>Imtihon fanlari boshqaruvi:</b>\n\nQuyidagi fanlardan birini tanlang yoki yangisini qo'shing:",
        reply_markup=get_subjects_manage_kb(subjects),
        parse_mode="HTML",
    )


@admin_subjects_router.callback_query(F.data == "adm_sub_list")
async def show_subjects_cb(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Fanlar ro'yxatiga qaytish"""
    await state.clear()
    await callback.answer()
    subjects = await SubjectService.get_subjects(session)
    if callback.message:
        await callback.message.edit_text(
            "📚 <b>Imtihon fanlari boshqaruvi:</b>\n\nFanlar ro'yxati:",
            reply_markup=get_subjects_manage_kb(subjects),
            parse_mode="HTML",
        )


@admin_subjects_router.callback_query(F.data == "adm_sub_add")
async def start_add_subject(callback: CallbackQuery, state: FSMContext) -> None:
    """Yangi fan qo'shish"""
    await callback.answer()
    await state.set_state(SubjectStates.waiting_name)
    if callback.message:
        await callback.message.edit_text(
            "📚 <b>Yangi fan qo'shish</b>\n\nFan nomini kiriting:\n<i>(Masalan: Kimyo, Biologiya, Matematika, Ingliz tili)</i>",
            parse_mode="HTML",
        )


@admin_subjects_router.message(SubjectStates.waiting_name)
async def process_subject_name(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Fan nomi saqlandi"""
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("⚠️ Fan nomi juda qisqa. Qaytadan kiriting:")
        return

    await state.clear()
    subject = await SubjectService.create_subject(session, name=name)
    subjects = await SubjectService.get_subjects(session)

    await message.answer(
        f"🎉 <b>Yangi fan muvaffaqiyatli qo'shildi!</b>\n\n📚 Fan: <b>{subject.name}</b>",
        reply_markup=get_subjects_manage_kb(subjects),
        parse_mode="HTML",
    )


@admin_subjects_router.callback_query(F.data.startswith("adm_sub_del:"))
async def delete_subject_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """Fanni o'chirish"""
    sub_id = int(callback.data.split(":")[1])
    deleted = await SubjectService.delete_subject(session, sub_id)
    if not deleted:
        await callback.answer(
            "⚠️ Ushbu fan bo'yicha imtihon seanslari mavjud bo'lgani sababli uni o'chirib bo'lmaydi!",
            show_alert=True,
        )
        return

    await callback.answer("Fan o'chirildi!", show_alert=True)

    subjects = await SubjectService.get_subjects(session)
    if callback.message:
        await callback.message.edit_text(
            "📚 <b>Imtihon fanlari:</b>\n\nFan o'chirildi. Yangilangan ro'yxat:",
            reply_markup=get_subjects_manage_kb(subjects),
            parse_mode="HTML",
        )

