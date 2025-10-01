from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.keyboards import categories_keyboard, confirm_keyboard, main_menu_keyboard, role_keyboard
from services.database import Database
from states import RegistrationStates

router = Router()
db = Database()


async def delete_lst_msgs(message: Message):
    await message.bot.delete_message(message.chat.id, message.message_id - 1)
    await message.bot.delete_message(message.chat.id, message.message_id)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user = await db.get_user(message.from_user.id)

    if user:
        await message.answer(
            f"С возвращением, {user['first_name']}!",
            reply_markup=main_menu_keyboard(await db.is_admin_or_moderator(message.from_user.id)),
        )
        return

    await message.answer("👋 Добро пожаловать! Для регистрации введите ваше имя:")
    await state.set_state(RegistrationStates.first_name)


@router.message(RegistrationStates.first_name, F.text)
async def process_first_name(message: Message, state: FSMContext):
    await delete_lst_msgs(message)

    await state.update_data(first_name=message.text)
    await message.answer("Отлично! Теперь введите вашу фамилию:")
    await state.set_state(RegistrationStates.last_name)


@router.message(RegistrationStates.last_name, F.text)
async def process_last_name(message: Message, state: FSMContext):
    await delete_lst_msgs(message)

    await state.update_data(last_name=message.text)
    await message.answer('Введите ваше отчество (или прочерк "-" при отсутствии):')
    await state.set_state(RegistrationStates.middle_name)


@router.message(RegistrationStates.middle_name, F.text)
async def process_middle_name(message: Message, state: FSMContext):
    await delete_lst_msgs(message)

    data = await state.get_data()
    data["middle_name"] = message.text if message.text != "-" else None
    await state.set_data(data)

    await message.answer("Выберите вашу роль:", reply_markup=role_keyboard())
    await state.set_state(RegistrationStates.select_role)


@router.callback_query(RegistrationStates.select_role, F.data.startswith("role_"))
async def process_role_selection(callback: CallbackQuery, state: FSMContext):
    role_type = callback.data.split("_")[1]
    await state.update_data(role=role_type)

    # Переходим к выбору категории
    await callback.message.edit_text("Выберите вашу категорию:", reply_markup=categories_keyboard())
    await state.set_state(RegistrationStates.select_category)
    await callback.answer()


# Обработчик выбора категории
@router.callback_query(RegistrationStates.select_category, F.data.startswith("category_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=category_id)

    # Получаем все данные для подтверждения
    data = await state.get_data()

    role_mapping = {"student": "🎓 Студент", "moderator": "👨‍🏫 Модератор", "admin": "👑 Администратор"}
    role_name = role_mapping.get(data["role"], "❓ Неизвестная роль")

    # Получаем название категории
    category_name = await db.get_category_name(category_id)

    user_data = (
        "Проверьте ваши данные:\n\n"
        f"👤 Имя: {data['first_name']}\n"
        f"📖 Фамилия: {data['last_name']}\n"
        f"📝 Отчество: {data.get('middle_name', 'не указано')}\n"
        f"🎭 Роль: {role_name}\n"
        f"🏷️ Категория: {category_name}"
    )

    await callback.message.edit_text(user_data, reply_markup=confirm_keyboard())
    await state.set_state(RegistrationStates.confirm_data)
    await callback.answer()


# Подтверждение регистрации
@router.callback_query(RegistrationStates.confirm_data, F.data == "confirm_yes")
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    try:
        role_mapping = {"student": "Студент", "moderator": "Модератор", "admin": "Администратор"}
        role_name = role_mapping.get(data.get("role", "student"), "Пользователь")

        await db.create_user(
            telegram_id=callback.from_user.id,
            first_name=data["first_name"],
            last_name=data["last_name"],
            middle_name=data.get("middle_name"),
            role=role_name,
            category_id=data.get("category_id"),
        )

        first_name = data["first_name"]
        category_name = await db.get_category_name(data.get("category_id", 0))

        await callback.message.edit_text(
            f"✅ Регистрация успешно завершена!\n\n"
            f"Добро пожаловать, {first_name}!\n"
            f"Ваша роль: {role_name}\n"
            f"Ваша категория: {category_name}\n\n"
            f"Теперь вы можете использовать все возможности бота.",
            reply_markup=None,
        )

        await callback.message.answer(
            "Выберите действие:", reply_markup=main_menu_keyboard(await db.is_admin_or_moderator(callback.from_user.id))
        )

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при сохранении данных: {str(e)}")
    finally:
        await state.clear()


@router.callback_query(RegistrationStates.confirm_data, F.data == "confirm_no")
async def restart_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Регистрация отменена. Начнём заново!")
    await cmd_start(callback.message, state)
