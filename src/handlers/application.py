from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.keyboards import (
    back_to_my_applications_keyboard,
    confirm_olimp_keyboard,
    main_menu_keyboard,
    my_applications_keyboard,
    olympiads_keyboard,
)
from services.database import Database
from states import ApplicationStates

router = Router()
db = Database()


@router.message(F.text == "🏆 Доступные олимпиады")
async def show_olympiads(message: Message):
    await message.bot.delete_message(message.chat.id, message.message_id)

    olympiads = await db.get_active_olympiads()

    if not olympiads:
        await message.answer("В данный момент нет доступных олимпиад")
        return

    await message.answer("Выберите олимпиаду для подачи заявки:", reply_markup=olympiads_keyboard(olympiads))


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
    subject_name = await db.get_subject_name(olympiad["subject_id"])

    # Формируем сообщение для подтверждения
    olympiad_info = (
        f"🏆 {olympiad['title']}\n"
        f"📚 Дисциплина: {subject_name}\n"
        f"🏢 Организатор: {olympiad['organizer']}\n"
        f"📅 Начало: {olympiad['start_date']}\n"
        f"📅 Окончание: {olympiad['end_date']}\n\n"
        f"{olympiad['description']}"
    )

    await callback.message.answer(olympiad_info, reply_markup=confirm_olimp_keyboard())
    await state.set_state(ApplicationStates.confirm_application)
    await callback.answer()


@router.callback_query(ApplicationStates.confirm_application, F.data == "application_confirm")
async def confirm_application(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    olympiad_id = data["olympiad_id"]

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
            reply_markup=main_menu_keyboard(await db.is_admin_or_moderator(callback.from_user.id)),
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при подаче заявки",
            reply_markup=main_menu_keyboard(await db.is_admin_or_moderator(callback.from_user.id)),
        )

    await state.clear()


@router.message(F.text == "📋 Мои заявки")
async def show_my_applications(message: Message):
    """Показывает список заявок пользователя с сообщениями модераторов"""
    # Получаем user_id пользователя
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return

    # Получаем заявки пользователя
    applications = await db.get_user_applications(user["user_id"])

    if not applications:
        await message.answer("У вас нет активных заявок")
        return

    # Формируем список заявок для клавиатуры
    app_list = []
    for app in applications:
        status_icon = (
            "🟡" if app["status_name"] == "Рассмотрение" else "🟢" if app["status_name"] == "Одобрена" else "🔴"
        )
        app_list.append(
            {"id": app["application_id"], "text": f"{status_icon} {app['olympiad_title']} ({app['status_name']})"}
        )

    await message.answer("📋 Ваши заявки:", reply_markup=my_applications_keyboard(app_list))


@router.callback_query(F.data.startswith("view_my_app_"))
async def view_my_application_details(callback: CallbackQuery):
    """Детальный просмотр заявки пользователя"""
    application_id = int(callback.data.split("_")[3])

    # Получаем детали заявки
    application = await db.get_application_details(application_id)
    if not application:
        await callback.answer("Заявка не найдена")
        return

    # Получаем сообщение модератора для этой заявки
    message = await db.get_application_moderator_message(application_id)

    # Форматируем информацию о заявке
    created_date = application["created_date"].strftime("%d.%m.%Y %H:%M")
    application_info = (
        f"📝 Заявка #{application_id}\n"
        f"🏆 Олимпиада: {application['olympiad_title']}\n"
        f"🔄 Статус: {application['status_name']}\n"
        f"📅 Дата подачи: {created_date}"
    )

    # Добавляем сообщение модератора если есть
    if message:
        application_info += f"\n\n💬 Сообщение модератора:\n{message['message_text']}"
    else:
        application_info += "\n\n💬 Сообщение модератора: пока отсутствует"

    await callback.message.answer(application_info, reply_markup=back_to_my_applications_keyboard())
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "back_to_my_applications")
async def back_to_my_applications(callback: CallbackQuery):
    """Возврат к списку заявок пользователя"""
    await callback.message.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.answer("❌ Пользователь не найден")
        return

    # Получаем заявки пользователя
    applications = await db.get_user_applications(user["user_id"])

    if not applications:
        await callback.message.answer("У вас нет активных заявок")
        return

    # Формируем список заявок для клавиатуры
    app_list = []
    for app in applications:
        status_icon = (
            "🟡" if app["status_name"] == "Рассмотрение" else "🟢" if app["status_name"] == "Одобрена" else "🔴"
        )
        app_list.append(
            {"id": app["application_id"], "text": f"{status_icon} {app['olympiad_title']} ({app['status_name']})"}
        )

    await callback.message.answer("📋 Ваши заявки:", reply_markup=my_applications_keyboard(app_list))
    await callback.answer()
