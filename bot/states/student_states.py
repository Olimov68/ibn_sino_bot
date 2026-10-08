from aiogram.fsm.state import State, StatesGroup


class StudentRegistrationStates(StatesGroup):
    waiting_full_name = State()
    waiting_phone = State()
    waiting_grade = State()


class StudentProfileStates(StatesGroup):
    waiting_edit_name = State()
    waiting_edit_phone = State()
    waiting_edit_grade = State()


class StudentBookingStates(StatesGroup):
    waiting_subject = State()
    waiting_date = State()
    waiting_time = State()
