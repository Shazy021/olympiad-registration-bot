from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    first_name = State()
    last_name = State()
    middle_name = State()
    select_role = State()
    select_category = State()
    confirm_data = State()