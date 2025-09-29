from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from states import EditProfileStates
from keyboards.keyboards import main_menu_keyboard, settings_keyboard
from services.database import Database
from keyboards.keyboards import (
    edit_profile_field_keyboard,
    get_categories_keyboard
)

router = Router()
db = Database()

@router.message(F.text == "🏠 Главное меню")
async def main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.bot.delete_message(message.chat.id, message.message_id)

    await message.answer(
        "Выберите действие:",
        reply_markup=main_menu_keyboard(await db.is_admin_or_moderator(message.from_user.id))
    )

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    await message.bot.delete_message(message.chat.id, message.message_id)

    # Проверяем роль пользователя
    is_admin = await db.is_admin(message.from_user.id)
    is_moderator = await db.is_moderator(message.from_user.id)
    
    # Базовая справка для всех пользователей
    help_text = (
        "ℹ️ Помощь по боту:\n\n"
        "🎯 **Основные функции:**\n"
        "• /start - Начать работу с ботом\n"
        "• /help - Получить эту справку\n"
        "• 👤 Профиль - Просмотр данных профиля\n"
        "• 📋 Мои заявки - Просмотр ваших заявок на олимпиады\n"
        "• 🏆 Доступные олимпиады - Список активных олимпиад\n"
        "• ⚙️ Настройки - Управление профилем\n"
        "• ✏️ Изменить профиль - Редактирование данных\n"
        "• ❌ Удалить аккаунт - Полное удаление профиля\n"
        "• 🏠 Главное меню - Вернуться в главное меню\n\n"
    )
    
    # Дополнительные функции для админов/модераторов
    if is_admin:
        help_text += (
            "🔧 **Функции администрирования:**\n"
            "• 👑 Админ-панель - Управление системой\n"
            "• 📝 Заявки на модерации - Обработка заявок\n"
            "• ➕ Добавить олимпиаду - Создание новых олимпиад\n"
            "• 📋 Список олимпиад - Управление олимпиадами\n"
            "• ✏️ Редактировать олимпиады - Изменение данных\n"
            "• 🗑️ Удалить олимпиады - Удаление мероприятий\n"
            "• 📊 Экспорт отчетов - Генерация Excel-отчетов\n"
            "• 🔄 Изменение статусов заявок - Одобрение/отклонение\n"
            "• 💬 Управление сообщениями - Комментарии к заявкам\n\n"
        )
    elif is_moderator:
        help_text += (
            "🔧 **Функции модерации:**\n"
            "• 👑 Админ-панель - Управление системой\n"
            "• 📝 Заявки на модерации - Обработка заявок\n\n"
        )
    
    help_text += (
        "❓ **Статусы заявок:**\n"
        "🟡 Рассмотрение - заявка проверяется\n"
        "🟢 Одобрена - участие подтверждено\n"
        "🔴 Отклонена - заявка не принята\n\n"
    )

    await message.answer(help_text, parse_mode="Markdown")

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

    # Получаем название роли и категории
    role_name = await db.get_role_name(user.get('user_id'))
    category_name = await db.get_category_name_by_user_id(user.get('user_id'))
    
    profile_text = (
        "👤 Ваш профиль:\n\n"
        f"🧑 Имя: {user['first_name']}\n"
        f"📖 Фамилия: {user['last_name']}\n"
        f"📝 Отчество: {user.get('middle_name', 'не указано')}\n"
        f"🎭 Роль: {role_name}\n"
        f"🏷️ Категория: {category_name}"
    )
    
    await message.answer(profile_text, reply_markup=main_menu_keyboard(await db.is_admin_or_moderator(message.from_user.id)))

@router.message(F.text == "✏️ Изменить профиль")
async def start_edit_profile(message: Message, state: FSMContext):
    """Начало процесса редактирования профиля"""
    await state.set_state(EditProfileStates.select_field)
    await message.answer(
        "Выберите поле, которое хотите изменить:",
        reply_markup=edit_profile_field_keyboard()
    )

@router.callback_query(EditProfileStates.select_field, F.data.startswith("profile_edit_field_"))
async def select_field_to_edit(callback: CallbackQuery, state: FSMContext):
    """Выбор поля для редактирования"""
    field = callback.data.split("_")[-1]
    await state.update_data(edit_field=field)
    
    field_names = {
        "first": "имя",
        "last": "фамилию",
        "middle": "отчество",
        "category": "категорию"
    }
    
    if field == "category":
        categories = await db.get_categories()
        await callback.message.answer(
            "Выберите новую категорию:",
            reply_markup=get_categories_keyboard(categories, is_edit=True)
        )
        await state.set_state(EditProfileStates.edit_category)
    else:
        await callback.message.answer(f"Введите новое {field_names.get(field, 'значение')}:")
        
        # Устанавливаем соответствующее состояние
        if field == "first":
            await state.set_state(EditProfileStates.edit_first_name)
        elif field == "last":
            await state.set_state(EditProfileStates.edit_last_name)
        elif field == "middle":
            await state.set_state(EditProfileStates.edit_middle_name)
    
    await callback.message.delete()
    await callback.answer()

@router.message(EditProfileStates.edit_first_name)
async def process_edit_first_name(message: Message, state: FSMContext):
    """Обработка нового имени"""
    success = await db.update_user_profile(
        message.from_user.id,
        first_name=message.text
    )
    
    if success:
        await message.answer("✅ Имя успешно обновлено!")
    else:
        await message.answer("❌ Ошибка при обновлении имени")
    
    await state.clear()

@router.message(EditProfileStates.edit_last_name)
async def process_edit_last_name(message: Message, state: FSMContext):
    """Обработка новой фамилии"""
    success = await db.update_user_profile(
        message.from_user.id,
        last_name=message.text
    )
    
    if success:
        await message.answer("✅ Фамилия успешно обновлена!")
    else:
        await message.answer("❌ Ошибка при обновлении фамилии")
    
    await state.clear()

@router.message(EditProfileStates.edit_middle_name)
async def process_edit_middle_name(message: Message, state: FSMContext):
    """Обработка нового отчества"""
    # Если пользователь ввел "-", сохраняем как None
    middle_name = message.text if message.text != "-" else None
    
    success = await db.update_user_profile(
        message.from_user.id,
        middle_name=middle_name
    )
    
    if success:
        await message.answer("✅ Отчество успешно обновлено!")
    else:
        await message.answer("❌ Ошибка при обновлении отчества")
    
    await state.clear()

@router.callback_query(EditProfileStates.edit_category, F.data.startswith("edit_cat_"))
async def process_edit_category(callback: CallbackQuery, state: FSMContext):
    """Обработка новой категории"""
    category_id = int(callback.data.split("_")[2])
    success = await db.update_user_profile(
        callback.from_user.id,
        category_id=category_id
    )
    
    if success:
        await callback.message.answer("✅ Категория успешно обновлена!")
    else:
        await callback.message.answer("❌ Ошибка при обновлении категории")
    
    await callback.message.delete()
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel_edit_profile")
async def cancel_edit_profile(callback: CallbackQuery, state: FSMContext):
    """Отмена редактирования профиля"""
    await state.clear()
    await callback.message.answer(
        "Редактирование профиля отменено",
        reply_markup=main_menu_keyboard(await db.is_admin_or_moderator(callback.from_user.id))
    )
    await callback.message.delete()
    await callback.answer()
