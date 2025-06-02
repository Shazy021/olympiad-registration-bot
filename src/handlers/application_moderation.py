from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from services.database import Database
from keyboards.keyboards import (
    application_list_keyboard,
    application_action_keyboard
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
async def approve_application(callback: CallbackQuery):
    application_id = int(callback.data.split("_")[2])
    success = await db.update_application_status(application_id, "Одобрена")
    
    if success:
        await callback.message.answer("✅ Заявка одобрена!")
        # Здесь можно добавить уведомление пользователю
    else:
        await callback.message.answer("❌ Ошибка при обновлении статуса")
    
    await callback.answer()

@router.callback_query(F.data.startswith("app_reject_"))
async def reject_application(callback: CallbackQuery):
    application_id = int(callback.data.split("_")[2])
    success = await db.update_application_status(application_id, "Отклонена")
    
    if success:
        await callback.message.answer("❌ Заявка отклонена")
        # Здесь можно добавить уведомление пользователю
    else:
        await callback.message.answer("❌ Ошибка при обновлении статуса")
    
    await callback.answer()

@router.callback_query(F.data.startswith("app_"))
async def show_application_details(callback: CallbackQuery):
    await callback.message.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    application_id = int(callback.data.split("_")[1])
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
        reply_markup=application_action_keyboard(application_id)
    )
    await callback.answer()


@router.callback_query(F.data == 'back_to_applications')
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