from aiogram.fsm.state import State, StatesGroup


class LocationStates(StatesGroup):
    waiting_name = State()
    waiting_address = State()


class RoomStates(StatesGroup):
    waiting_location = State()
    waiting_name = State()
    waiting_capacity = State()
    waiting_sort_order = State()
    # Tahrirlash uchun
    waiting_edit_name = State()
    waiting_edit_capacity = State()


class SubjectStates(StatesGroup):
    waiting_name = State()


class SessionStates(StatesGroup):
    waiting_subject = State()
    waiting_location = State()
    waiting_date = State()
    waiting_time = State()


class BroadcastStates(StatesGroup):
    waiting_session = State()
    waiting_text = State()
    waiting_confirm = State()


class AdminManagementStates(StatesGroup):
    waiting_telegram_id = State()
    waiting_full_name = State()


class ChannelStates(StatesGroup):
    waiting_channel_identifier = State()
    waiting_channel_title = State()
    waiting_invite_link = State()

