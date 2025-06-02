from aiogram import Router, F
from aiogram.types import Message
from keyboards.keyboards import main_menu_keyboard, settings_keyboard
from services.database import Database

router = Router()
db = Database()

@router.message(F.text == "🏠 Главное меню")
async def main_menu(message: Message):
    await message.bot.delete_message(message.chat.id, message.message_id)

    await message.answer(
        "Выберите действие:",
        reply_markup=main_menu_keyboard(await db.is_admin_or_moderator(message.from_user.id))
    )

@router.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    await message.bot.delete_message(message.chat.id, message.message_id)

    await message.answer(
        "ℹ️ Помощь по боту:\n\n"
        "• /start - Начать работу\n"
        "• /help - Получить помощь\n"
        "• 📋 Мои заявки - Просмотр ваших заявок\n"
        "• 🏆 Доступные олимпиады - Список олимпиад\n"
        "• ⚙️ Настройки - Настройки профиля\n"
        "• 🏠 Главное меню - Вернуться в главное меню"
    )

@router.message(F.text == "⚙️ Настройки")
async def settings_command(message: Message):
    await message.bot.delete_message(message.chat.id, message.message_id)

    await message.answer(
        "⚙️ Настройки профиля:",
        reply_markup=settings_keyboard()
    )

@router.message(F.text == "👤 Профиль")
async def view_profile(message: Message):
    await message.bot.delete_message(message.chat.id, message.message_id)

    user = await db.get_user(message.from_user.id)
    print(user)

    # Получаем название роли и категории
    role_name = await db.get_role_name(user.get('user_id'))
    category_name = await db.get_category_name_by_user_id(user.get('user_id'))
    
    profile_text = (
        "👤 Ваш профиль:\n\n"
        f"▫️ Имя: {user['first_name']}\n"
        f"▫️ Фамилия: {user['last_name']}\n"
        f"▫️ Отчество: {user.get('middle_name', 'не указано')}\n"
        f"▫️ Роль: {role_name}\n"
        f"▫️ Категория: {category_name}"
    )
    
    await message.answer(profile_text, reply_markup=main_menu_keyboard(await db.is_admin_or_moderator(message.from_user.id)))

# Добавим обработчики для остальных пунктов меню позже