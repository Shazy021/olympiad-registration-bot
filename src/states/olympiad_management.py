from aiogram.fsm.state import State, StatesGroup

class AddOlympiadStates(StatesGroup):
    title = State()
    description = State()
    organizer = State()
    start_date = State()
    end_date = State()
    select_subject = State()
    confirm_data = State()

class ApplicationStates(StatesGroup):
    select_olympiad = State()
    confirm_application = State()

class ApplicationModerationStates(StatesGroup):
    view_application = State()
    change_status = State()

class EditOlympiadStates(StatesGroup):
    select_field = State()
    edit_title = State()
    edit_description = State()
    edit_organizer = State()
    edit_start_date = State()
    edit_end_date = State()
    edit_subject = State()
