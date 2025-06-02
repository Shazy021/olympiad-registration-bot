from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from services.database import Database
from states import ApplicationStates
from keyboards.keyboards import (
    olympiads_keyboard,
    main_menu_keyboard,
    confirm_olimp_keyboard
)

router = Router()
db = Database()

@router.message(F.text == "🏆 Доступные олимпиады")
async def show_olympiads(message: Message):
    await message.bot.delete_message(message.chat.id, message.message_id)

    olympiads = await db.get_active_olympiads()
    
    if not olympiads:
        await message.answer("В данный момент нет доступных олимпиад")
        return
        
    await message.answer(
        "Выберите олимпиаду для подачи заявки:",
        reply_markup=olympiads_keyboard(olympiads)
    )

@router.callback_query(F.data.startswith("olympiad_"))
async def select_olympiad(callback: CallbackQuery, state: FSMContext):
    olympiad_id = int(callback.data.split("_")[1])
    await state.update_data(olympiad_id=olympiad_id)
    
    # Получаем данные об олимпиаде
    olympiad = await db.get_olympiad_by_id(olympiad_id)
    
    if not olympiad:
        await callback.message.answer("Ошибка: олимпиада не найдена")
        await state.clear()
        return
        
    # Получаем название дисциплины
    subject_name = await db.get_subject_name(olympiad['subject_id'])
    
    # Формируем сообщение для подтверждения
    olympiad_info = (
        f"🏆 {olympiad['title']}\n"
        f"📚 Дисциплина: {subject_name}\n"
        f"🏢 Организатор: {olympiad['organizer']}\n"
        f"📅 Начало: {olympiad['start_date']}\n"
        f"📅 Окончание: {olympiad['end_date']}\n\n"
        f"{olympiad['description']}"
    )
    
    await callback.message.answer(
        olympiad_info,
        reply_markup=confirm_olimp_keyboard()
    )
    await state.set_state(ApplicationStates.confirm_application)
    await callback.answer()

@router.callback_query(ApplicationStates.confirm_application, F.data == "application_confirm")
async def confirm_application(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    olympiad_id = data['olympiad_id']
    
    # Проверяем, не подана ли уже заявка
    if await db.has_application(user_id, olympiad_id):
        await callback.message.answer("Вы уже подавали заявку на эту олимпиаду")
        await state.clear()
        return
        
    # Создаем заявку
    success = await db.create_application(user_id, olympiad_id)
    
    if success:
        await callback.message.answer(
            "✅ Заявка успешно подана! Ожидайте подтверждения.",
            reply_markup=main_menu_keyboard(await db.is_admin_or_moderator(callback.from_user.id))
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при подаче заявки",
            reply_markup=main_menu_keyboard(await db.is_admin_or_moderator(callback.from_user.id))
        )
    
    await state.clear()

@router.message(F.text == "📋 Мои заявки")
async def show_my_applications(message: Message):
    applications = db.get_user_applications(message.from_user.id)
    
    if not applications:
        await message.answer("У вас нет активных заявок")
        return
    
    text = "Ваши заявки:\n\n"
    for app in applications:
        text += f"🏆 {app['olympiad_title']}\n"
        text += f"📅 {app['registration_date']}\n"
        text += f"🔄 Статус: {app['status']}\n\n"
    
    await message.answer(text)
    