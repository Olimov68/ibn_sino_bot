"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-08 12:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. admins
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id", name="uq_admins_telegram_id"),
    )

    # 2. locations
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. rooms
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "name", name="uq_room_location_name"),
        sa.CheckConstraint("capacity > 0", name="chk_room_capacity_positive"),
    )

    # 4. subjects
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_subjects_name"),
    )

    # 5. exam_sessions
    op.create_table(
        "exam_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("mode", sa.Text(), server_default="offline", nullable=False),
        sa.Column("status", sa.Text(), server_default="open", nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject_id", "location_id", "exam_date", "start_time", name="uq_session_subject_location_datetime"),
        sa.CheckConstraint("mode IN ('offline', 'online')", name="chk_session_mode"),
        sa.CheckConstraint("status IN ('open', 'full', 'closed')", name="chk_session_status"),
    )

    # 6. students
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("grade", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id", name="uq_students_telegram_id"),
        sa.UniqueConstraint("phone", name="uq_students_phone"),
    )

    # 7. registrations
    op.create_table(
        "registrations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("seat_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["exam_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("seat_no > 0", name="chk_reg_seat_positive"),
        sa.CheckConstraint("status IN ('active', 'cancelled')", name="chk_reg_status"),
    )

    # Partial unique indexes & query indexes
    op.create_index(
        "uq_student_session",
        "registrations",
        ["student_id", "session_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "uq_seat",
        "registrations",
        ["session_id", "room_id", "seat_no"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "idx_reg_session",
        "registrations",
        ["session_id", "room_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_reg_session", table_name="registrations")
    op.drop_index("uq_seat", table_name="registrations")
    op.drop_index("uq_student_session", table_name="registrations")
    op.drop_table("registrations")
    op.drop_table("students")
    op.drop_table("exam_sessions")
    op.drop_table("subjects")
    op.drop_table("rooms")
    op.drop_table("locations")
    op.drop_table("admins")
