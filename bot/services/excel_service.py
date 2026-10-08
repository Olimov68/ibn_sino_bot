import io
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db.models.registration import Registration
from bot.db.models.room import Room
from bot.db.models.session import ExamSession
from bot.db.models.student import Student


class ExcelService:
    @staticmethod
    async def generate_attendance_sheet(
        session: AsyncSession,
        session_id: int,
    ) -> io.BytesIO:
        """
        Imtihon seansi uchun xona va stol bo'yicha davomat ro'yxatini Excel (.xlsx) formatida shakllantirish
        """
        # Seans ma'lumotlarini olish
        exam_session = await session.get(
            ExamSession,
            session_id,
            options=[
                selectinload(ExamSession.subject),
                selectinload(ExamSession.location),
            ],
        )
        if not exam_session:
            raise ValueError("Imtihon seansi topilmadi")

        # Ro'yxatdan o'tgan o'quvchilarni olish
        reg_query = (
            select(Registration)
            .where(
                Registration.session_id == session_id,
                Registration.status == "active",
            )
            .join(Registration.room)
            .options(
                selectinload(Registration.student),
                selectinload(Registration.room),
            )
            .order_by(Room.sort_order.asc(), Room.name.asc(), Registration.seat_no.asc())
        )
        registrations = list((await session.execute(reg_query)).scalars().all())

        # Excel kitobi yaratish
        wb = Workbook()
        ws = wb.active
        ws.title = "Davomat varaqasi"

        # Uslublar (Styles)
        font_title = Font(name="Calibri", size=14, bold=True, color="1F497D")
        font_meta = Font(name="Calibri", size=11, bold=True)
        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        font_data = Font(name="Calibri", size=11)

        fill_header = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        fill_room_section = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")

        align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        align_left = Alignment(horizontal="left", vertical="center")
        align_right = Alignment(horizontal="right", vertical="center")

        thin_side = Side(border_style="thin", color="A6B9D0")
        border_box = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        # 1. Sarlavha qismi
        ws.merge_cells("A1:G1")
        title_cell = ws["A1"]
        title_cell.value = "IBN SINO MAKTABI — IMTIHON DAVOMAT VARAQASI"
        title_cell.font = font_title
        title_cell.alignment = align_center
        ws.row_dimensions[1].height = 25

        # 2. Metama'lumotlar
        date_str = exam_session.exam_date.strftime("%d.%m.%Y")
        time_str = exam_session.start_time.strftime("%H:%M")

        ws["A3"] = "📚 Fan:"
        ws["B3"] = exam_session.subject.name
        ws["A4"] = "📅 Sana:"
        ws["B4"] = date_str
        ws["D3"] = "🕑 Vaqt:"
        ws["E3"] = time_str
        ws["D4"] = "📍 Manzil:"
        ws["E4"] = f"{exam_session.location.name} ({exam_session.location.address})"
        ws["A5"] = "👥 Jami o'quvchilar:"
        ws["B5"] = len(registrations)

        for row in range(3, 6):
            ws[f"A{row}"].font = font_meta
            ws[f"D{row}"].font = font_meta

        # 3. Jadval sarlavhasi
        headers = [
            "T/r",
            "Xona",
            "Stol №",
            "F.I.Sh (O'quvchi)",
            "Telefon raqami",
            "Sinf",
            "Imzo / Davomat",
        ]
        start_row = 7
        ws.row_dimensions[start_row].height = 24

        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=col_idx, value=header)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_center
            cell.border = border_box

        # 4. Ma'lumotlarni yozish
        current_row = start_row + 1
        current_room_name = None

        for idx, reg in enumerate(registrations, 1):
            # Agar xona o'zgarsa, ajratuvchi oraliq qator qo'yish
            if current_room_name != reg.room.name:
                current_room_name = reg.room.name
                ws.row_dimensions[current_row].height = 20
                ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=7)
                sec_cell = ws.cell(row=current_row, column=1, value=f"🚪 Xona: {current_room_name}")
                sec_cell.font = Font(name="Calibri", size=11, bold=True, color="1F497D")
                sec_cell.fill = fill_room_section
                sec_cell.alignment = align_left
                for col_idx in range(1, 8):
                    ws.cell(row=current_row, column=col_idx).border = border_box
                current_row += 1

            ws.row_dimensions[current_row].height = 20
            row_data = [
                idx,
                reg.room.name,
                reg.seat_no,
                reg.student.full_name,
                reg.student.phone or "—",
                f"{reg.student.grade}-sinf" if reg.student.grade else "—",
                "",  # Imzo uchun bo'sh joy
            ]

            for col_idx, val in enumerate(row_data, 1):
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                cell.font = font_data
                cell.border = border_box
                if col_idx in [1, 2, 3, 6]:
                    cell.alignment = align_center
                elif col_idx in [4]:
                    cell.alignment = align_left
                else:
                    cell.alignment = align_center

            current_row += 1

        # Ustun kengliklarini avtomatik moslash
        column_widths = {
            1: 8,   # T/r
            2: 14,  # Xona
            3: 10,  # Stol №
            4: 30,  # F.I.Sh
            5: 18,  # Telefon
            6: 12,  # Sinf
            7: 18,  # Imzo
        }
        for col_idx, width in column_widths.items():
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = width

        # Natijani BytesIO oqimiga saqlash
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output
