from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter

from states import RegistrationStates
from models import User
from services.database import Database
from keyboards.keyboards import main_menu_keyboard, role_keyboard, confirm_keyboard

router = Router()
db = Database()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user = await db.get_user(message.from_user.id)
    
    if user:
        await message.answer(
            f"С возвращением, {user['first_name']}!",
            reply_markup=main_menu_keyboard()
        )
        return
        
    await message.answer("👋 Добро пожаловать! Для регистрации введите ваше имя:")
    await state.set_state(RegistrationStates.first_name)

@router.message(RegistrationStates.first_name, F.text)
async def process_first_name(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Отлично! Теперь введите вашу фамилию:")
    await state.set_state(RegistrationStates.last_name)
    await message.delete()

@router.message(RegistrationStates.last_name, F.text)
async def process_last_name(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.answer("Введите ваше отчество (если есть):")
    await state.set_state(RegistrationStates.middle_name)
    await message.delete()

@router.message(RegistrationStates.middle_name, F.text)
async def process_middle_name(message: Message, state: FSMContext):
    data = await state.get_data()
    data['middle_name'] = message.text if message.text != "-" else None
    await state.set_data(data)
    
    await message.answer(
        "Выберите вашу роль:",
        reply_markup=role_keyboard()
    )
    await state.set_state(RegistrationStates.select_role)

@router.callback_query(
    RegistrationStates.select_role,
    F.data.startswith("role_")
)
async def process_role_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора роли пользователем"""
    role_type = callback.data.split("_")[1]
    await state.update_data(role=role_type)
    
    # Получаем все данные из состояния
    data = await state.get_data()
    
    # Форматируем название роли для отображения
    role_mapping = {
        "student": "🎓 Студент",
        "teacher": "👨‍🏫 Преподаватель",
        "admin": "👑 Администратор"
    }
    role_name = role_mapping.get(role_type, "❓ Неизвестная роль")
    
    # Формируем сообщение для подтверждения
    user_data = (
        "Проверьте ваши данные:\n\n"
        f"👤 Имя: {data['first_name']}\n"
        f"📖 Фамилия: {data['last_name']}\n"
        f"📝 Отчество: {data.get('middle_name', 'не указано')}\n"
        f"🎭 Роль: {role_name}"
    )
    
    # Обновляем сообщение с данными и кнопками подтверждения
    await callback.message.edit_text(
        user_data,
        reply_markup=confirm_keyboard()
    )
    await state.set_state(RegistrationStates.confirm_data)
    await callback.answer()


@router.callback_query(
    RegistrationStates.confirm_data, 
    F.data == "confirm_yes"
)
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    """Подтверждение регистрации и сохранение данных в БД"""
    data = await state.get_data()
    
    # Создаем пользователя в базе данных
    try:
        await db.create_user(
            telegram_id=callback.from_user.id,
            first_name=data['first_name'],
            last_name=data['last_name'],
            middle_name=data.get('middle_name'),
            role=data.get('role', 'student')
        )
        
        # Получаем имя пользователя для приветствия
        first_name = data['first_name']
        
        # Форматируем название роли для приветствия
        role_mapping = {
            "student": "Студент",
            "teacher": "Преподаватель",
            "admin": "Администратор"
        }
        role_name = role_mapping.get(data.get('role', 'student'), "Пользователь")
        
        # Отправляем приветствие
        await callback.message.edit_text(
            f"✅ Регистрация успешно завершена!\n\n"
            f"Добро пожаловать, {first_name}!\n"
            f"Ваша роль: {role_name}\n\n"
            f"Теперь вы можете использовать все возможности бота.",
            reply_markup=None
        )
        
        # Показываем главное меню
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard()
        )
        
    except Exception as e:
        await callback.message.answer(
            f"❌ Ошибка при сохранении данных: {str(e)}"
        )
    finally:
        # Очищаем состояние независимо от результата
        await state.clear()

@router.callback_query(
    RegistrationStates.confirm_data, 
    F.data == "confirm_no"
)
async def restart_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Регистрация отменена. Начнём заново!")
    await cmd_start(callback.message, state)