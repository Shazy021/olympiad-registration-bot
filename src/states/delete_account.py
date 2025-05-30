from aiogram.fsm.state import State, StatesGroup

class DeleteAccountStates(StatesGroup):
    confirm_delete = State()