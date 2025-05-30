from aiogram import Router, F
from aiogram.types import Message
from keyboards.keyboards import main_menu_keyboard

router = Router()

@router.message(F.text == "🏠 Главное меню")
async def main_menu(message: Message):
    await message.answer(
        "Выберите действие:",
        reply_markup=main_menu_keyboard()
    )

@router.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    await message.answer(
        "ℹ️ Помощь по боту:\n\n"
        "• /start - Начать работу\n"
        "• /help - Получить помощь\n"
        "• 📋 Мои заявки - Просмотр ваших заявок\n"
        "• 🏆 Доступные олимпиады - Список олимпиад\n"
        "• ⚙️ Настройки - Настройки профиля\n"
        "• 🏠 Главное меню - Вернуться в главное меню"
    )

# Добавим обработчики для остальных пунктов меню позже