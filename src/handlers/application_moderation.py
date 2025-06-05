from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from services.database import Database
from states import ModerationStates
from keyboards.keyboards import (
    application_list_keyboard,
    moder_application_action_keyboard,
    skip_comment_keyboard
)

router = Router()
db = Database()

@router.message(F.text == "📝 Заявки на модерации")
async def show_pending_applications(message: Message):
    if not await db.is_admin_or_moderator(message.from_user.id):
        return
        
    applications = await db.get_pending_applications()
    
    if not applications:
        await message.answer("Нет заявок, ожидающих модерации")
        return
        
    await message.answer(
        "Заявки, ожидающие модерации:",
        reply_markup=application_list_keyboard(applications)
    )

@router.callback_query(F.data.startswith("app_approve_"))
async def approve_application(callback: CallbackQuery, state: FSMContext):
    application_id = int(callback.data.split("_")[2])
    await state.update_data(application_id=application_id, action="Одобрена")
    await callback.message.answer(
        "Введите сообщение для заявки (или нажмите 'Пропустить'):",
        reply_markup=skip_comment_keyboard()
    )
    await state.set_state(ModerationStates.waiting_comment)
    await callback.answer()

@router.callback_query(F.data.startswith("app_reject_"))
async def reject_application(callback: CallbackQuery, state: FSMContext):
    application_id = int(callback.data.split("_")[2])
    await state.update_data(application_id=application_id, action="reject")
    await callback.message.answer(
        "Введите сообщение для заявки (или нажмите 'Пропустить'):",
        reply_markup=skip_comment_keyboard()
    )
    await state.set_state(ModerationStates.waiting_comment)
    await callback.answer()

@router.callback_query(ModerationStates.waiting_comment, F.data == "skip_comment")
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    application_id = data['application_id']
    action = data['action']
    
    # Обновляем статус без комментария
    status = "Одобрена" if action == "Одобрена" else "Отклонена"
    success = await db.update_application_status(application_id, status)
    
    if success:
        status_icon = "✅" if action == "Одобрена" else "❌"
        await callback.message.answer(f"{status_icon} Заявка {status.lower()}!")
    else:
        await callback.message.answer("❌ Ошибка при обновлении статуса")
    
    await state.clear()
    await callback.answer()

@router.message(ModerationStates.waiting_comment)
async def process_moderation_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    application_id = data['application_id']
    action = data['action']
    
    # Обновляем статус
    status = "Одобрена" if action == "Одобрена" else "Отклонена"
    success = await db.update_application_status(application_id, status)
    
    if not success:
        await message.answer("❌ Ошибка при обновлении статуса")
        await state.clear()
        return
    
    # Получаем user_id модератора
    moderator = await db.get_user(message.from_user.id)
    
    # Сохраняем сообщение
    success = await db.create_message(
        user_id=moderator['user_id'],
        application_id=application_id,
        message_text=message.text
    )
    
    if success:
        status_icon = "✅" if action == "Одобрена" else "❌"
        await message.answer(f"{status_icon} Заявка {status.lower()} с комментарием!")
    else:
        await message.answer(f"✅ Статус обновлен, но не удалось сохранить комментарий")
    
    await state.clear()

@router.callback_query(F.data.startswith("app_id_"))
async def show_application_details(callback: CallbackQuery):
    await callback.message.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    application_id = int(callback.data.split("_")[2])
    application = await db.get_application_details(application_id)
    
    if not application:
        await callback.message.answer("Заявка не найдена")
        return
        
    # Форматируем информацию о заявке
    application_info = (
        f"📝 Заявка #{application_id}\n"
        f"👤 Пользователь: {application['first_name']} {application['last_name']}\n"
        f"📚 Олимпиада: {application['olympiad_title']}\n"
        f"📅 Дата подачи: {application['created_date']}\n"
        f"🔄 Статус: {application['status_name']}"
    )
    
    await callback.message.answer(
        application_info,
        reply_markup=moder_application_action_keyboard(application_id)
    )
    await callback.answer()


@router.callback_query(F.data == 'back_to_applications_moderation')
async def back_application(callback: Message):
    await callback.message.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    applications = await db.get_pending_applications()
    
    if not applications:
        await callback.message.answer("Нет заявок, ожидающих модерации")
        return
    
    await callback.message.answer(
        "Заявки, ожидающие модерации:",
        reply_markup=application_list_keyboard(applications)
    )