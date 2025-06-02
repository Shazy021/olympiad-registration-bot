from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from services.database import Database
from states import AddOlympiadStates
from keyboards.keyboards import (
    admin_main_keyboard,
    subjects_keyboard,
    confirm_keyboard,
    back_to_admin_menu_keyboard
)

router = Router()
db = Database()

async def is_admin_or_moderator(telegram_id: int) -> bool:
    return await db.is_admin_or_moderator(telegram_id)

async def delete_lst_msgs(message: Message):
    await message.bot.delete_message(message.chat.id, message.message_id - 1)
    await message.bot.delete_message(message.chat.id, message.message_id)


@router.message(F.text == "👑 Админ-панель")
async def admin_panel(message: Message):
    if not await is_admin_or_moderator(message.from_user.id):
        await message.answer("Доступ запрещен!")
        return
        
    await message.answer(
        "👑 Панель администратора:",
        reply_markup=admin_main_keyboard()
    )

@router.message(F.text == "➕ Добавить олимпиаду")
async def start_adding_olympiad(message: Message, state: FSMContext):
    if not await is_admin_or_moderator(message.from_user.id):
        return
        
    await message.answer("Введите название олимпиады:")
    await state.set_state(AddOlympiadStates.title)

@router.message(AddOlympiadStates.title)
async def process_title(message: Message, state: FSMContext):
    await delete_lst_msgs(message)

    await state.update_data(title=message.text)
    await message.answer("Введите описание олимпиады:")
    await state.set_state(AddOlympiadStates.description)

@router.message(AddOlympiadStates.description)
async def process_description(message: Message, state: FSMContext):
    await delete_lst_msgs(message)

    await state.update_data(description=message.text)
    await message.answer("Введите организатора олимпиады:")
    await state.set_state(AddOlympiadStates.organizer)

@router.message(AddOlympiadStates.organizer)
async def process_organizer(message: Message, state: FSMContext):
    await delete_lst_msgs(message)

    await state.update_data(organizer=message.text)
    await message.answer("Введите дату начала олимпиады (в формате ГГГГ-ММ-ДД):")
    await state.set_state(AddOlympiadStates.start_date)

@router.message(AddOlympiadStates.start_date)
async def process_start_date(message: Message, state: FSMContext):
    await delete_lst_msgs(message)

    date_text = message.text.strip()
    try:
        start_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("❌ Неверный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД:")
        return
    
    await state.update_data(start_date=start_date)
    await message.answer("Введите дату окончания олимпиады (в формате ГГГГ-ММ-ДД):")
    await state.set_state(AddOlympiadStates.end_date)

@router.message(AddOlympiadStates.end_date)
async def process_end_date(message: Message, state: FSMContext):
    await delete_lst_msgs(message)

    date_text = message.text.strip()
    try:
        end_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("❌ Неверный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД:")
        return

    data = await state.get_data()
    start_date = data['start_date']

    if end_date < start_date:
        await message.answer("❌ Дата окончания не может быть раньше даты начала. Пожалуйста, введите корректную дату окончания:")
        return
    
    await state.update_data(end_date=end_date)
    
    # Получаем список дисциплин для выбора
    subjects = await db.get_subjects()
    await message.answer(
        "Выберите дисциплину:",
        reply_markup=subjects_keyboard(subjects)
    )
    await state.set_state(AddOlympiadStates.select_subject)

@router.callback_query(AddOlympiadStates.select_subject, F.data.startswith("subject_"))
async def process_subject(callback: CallbackQuery, state: FSMContext):
    subject_id = int(callback.data.split("_")[1])
    await state.update_data(subject_id=subject_id)
    
    # Получаем все данные
    data = await state.get_data()
    
    # Получаем название дисциплины
    subject_name = await db.get_subject_name(subject_id)
    
    # Формируем сообщение для подтверждения
    olympiad_data = (
        "Проверьте данные олимпиады:\n\n"
        f"🏆 Название: {data['title']}\n"
        f"📝 Описание: {data['description']}\n"
        f"🏢 Организатор: {data['organizer']}\n"
        f"📅 Начало: {data['start_date']}\n"
        f"📅 Окончание: {data['end_date']}\n"
        f"📚 Дисциплина: {subject_name}"
    )
    
    await callback.message.answer(
        olympiad_data,
        reply_markup=confirm_keyboard()
    )
    await state.set_state(AddOlympiadStates.confirm_data)
    await callback.answer()

@router.callback_query(AddOlympiadStates.confirm_data, F.data == "confirm_yes")
async def confirm_olympiad(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Сохраняем олимпиаду в БД
    success = await db.create_olympiad(
        title=data['title'],
        description=data['description'],
        organizer=data['organizer'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        subject_id=data['subject_id']
    )
    
    if success:
        await callback.message.answer(
            "✅ Олимпиада успешно добавлена!",
            reply_markup=back_to_admin_menu_keyboard()
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при сохранении олимпиады",
            reply_markup=back_to_admin_menu_keyboard()
        )
    
    await state.clear()

@router.callback_query(
    AddOlympiadStates.confirm_data, 
    F.data == "confirm_no"
)
async def restart_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Регистрация отменена.")
    await start_adding_olympiad('➕ Добавить олимпиаду', state)