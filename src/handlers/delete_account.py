from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from states.delete_account import DeleteAccountStates
from services.database import Database
from keyboards.keyboards import confirm_delete_keyboard_del_acc

router = Router()
db = Database()

@router.message(Command("delete_account"))
@router.message(F.text == "❌ Удалить аккаунт")
async def cmd_delete_account(message: Message, state: FSMContext):
    """Запрос подтверждения удаления аккаунта"""
    await message.answer(
        "⚠️ Вы уверены, что хотите удалить свой аккаунт?\n\n"
        "Это действие:\n"
        "- Удалит все ваши данные\n"
        "- Отменит все ваши заявки\n"
        "- Необратимо!\n\n"
        "Подтвердите удаление:",
        reply_markup=confirm_delete_keyboard_del_acc()
    )
    await state.set_state(DeleteAccountStates.confirm_delete)

@router.callback_query(
    DeleteAccountStates.confirm_delete,
    F.data == "delete_yes"
)
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления аккаунта"""
    if await db.delete_user(callback.from_user.id):
        await callback.message.edit_text(
            "✅ Ваш аккаунт успешно удален!\n\n"
            "Если захотите вернуться, просто отправьте /start"
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось удалить аккаунт. Попробуйте позже."
        )
    
    await state.clear()
    await callback.answer()

@router.callback_query(
    DeleteAccountStates.confirm_delete,
    F.data == "delete_no"
)
async def cancel_delete(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления аккаунта"""
    await callback.message.edit_text("❌ Удаление аккаунта отменено.")
    await state.clear()
    await callback.answer()