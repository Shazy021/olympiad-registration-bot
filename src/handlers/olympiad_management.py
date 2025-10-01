import os
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from keyboards.keyboards import (
    admin_main_keyboard,
    application_action_keyboard,
    application_status_change_keyboard,
    back_to_admin_menu_keyboard,
    confirm_delete_keyboard,
    confirm_keyboard,
    edit_olympiad_field_keyboard,
    moderator_main_keyboard,
    olympiad_applications_keyboard,
    olympiad_detail_keyboard,
    olympiads_list_keyboard,
    subjects_keyboard,
)
from services.database import Database
from services.excel_export import generate_olympiad_report
from states import AddOlympiadStates, EditApplicationMessage, EditOlympiadStates

router = Router()
db = Database()


async def delete_lst_msgs(message: Message):
    await message.bot.delete_message(message.chat.id, message.message_id - 1)
    await message.bot.delete_message(message.chat.id, message.message_id)


@router.message(F.text == "👑 Админ-панель")
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()

    if not await db.is_admin_or_moderator(message.from_user.id):
        await message.answer("Доступ запрещен!")
        return
    elif await db.is_admin(message.from_user.id):
        await message.answer("👑 Панель администратора:", reply_markup=admin_main_keyboard())
    elif await db.is_moderator(message.from_user.id):
        await message.answer("👑 Панель модератора:", reply_markup=moderator_main_keyboard())


@router.message(F.text == "➕ Добавить олимпиаду")
async def start_adding_olympiad(message: Message, state: FSMContext):
    if not await db.is_admin_or_moderator(message.from_user.id):
        return

    await message.answer("Введите название олимпиады или перейдите в главное меню для отмены:")
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
    start_date = data["start_date"]

    if end_date < start_date:
        await message.answer(
            "❌ Дата окончания не может быть раньше даты начала. Пожалуйста, введите корректную дату окончания:"
        )
        return

    await state.update_data(end_date=end_date)

    # Получаем список дисциплин для выбора
    subjects = await db.get_subjects()
    await message.answer("Выберите дисциплину:", reply_markup=subjects_keyboard(subjects))
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

    await callback.message.answer(olympiad_data, reply_markup=confirm_keyboard())
    await state.set_state(AddOlympiadStates.confirm_data)
    await callback.answer()


@router.callback_query(AddOlympiadStates.confirm_data, F.data == "confirm_yes")
async def confirm_olympiad(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # Сохраняем олимпиаду в БД
    success = await db.create_olympiad(
        title=data["title"],
        description=data["description"],
        organizer=data["organizer"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        subject_id=data["subject_id"],
    )

    if success:
        await callback.message.answer("✅ Олимпиада успешно добавлена!", reply_markup=back_to_admin_menu_keyboard())
    else:
        await callback.message.answer("❌ Ошибка при сохранении олимпиады", reply_markup=back_to_admin_menu_keyboard())

    await state.clear()


@router.callback_query(AddOlympiadStates.confirm_data, F.data == "confirm_no")
async def restart_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Регистрация отменена.")
    await start_adding_olympiad("➕ Добавить олимпиаду", state)


@router.message(F.text == "📋 Список олимпиад")
async def list_olympiads(message: Message):
    """Показывает список всех олимпиад"""
    if not await db.is_admin_or_moderator(message.from_user.id):
        return

    olympiads = await db.get_all_olympiads()

    if not olympiads:
        await message.answer("Список олимпиад пуст")
        return

    await message.answer("📋 Список всех олимпиад:", reply_markup=olympiads_list_keyboard(olympiads, page=0))


@router.callback_query(F.data.startswith("olympiads_page_"))
async def change_olympiads_page(callback: CallbackQuery):
    """Обработка пагинации списка олимпиад"""
    page = int(callback.data.split("_")[2])
    olympiads = await db.get_all_olympiads()

    await callback.message.edit_reply_markup(reply_markup=olympiads_list_keyboard(olympiads, page))
    await callback.answer()


@router.callback_query(F.data.startswith("view_olympiad_apps_"))
async def view_olympiad_applications(callback: CallbackQuery):
    """Просмотр заявок на конкретную олимпиаду"""
    olympiad_id = int(callback.data.split("_")[3])
    applications = await db.get_applications_for_olympiad(olympiad_id)

    if not applications:
        await callback.answer("На эту олимпиаду нет заявок")
        return

    olympiad = await db.get_olympiad_by_id(olympiad_id)
    title = olympiad["title"] if olympiad else f"Олимпиада #{olympiad_id}"

    await callback.message.answer(
        f"📋 Заявки на олимпиаду: {title}", reply_markup=olympiad_applications_keyboard(applications, olympiad_id)
    )
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("app_admin_app_check_"))
async def view_application_admin(callback: CallbackQuery):
    """Детальный просмотр заявки для администратора"""
    application_id = int(callback.data.split("_")[-1])
    application = await db.get_application_details(application_id)

    if not application:
        await callback.answer("Заявка не найдена")
        return

    messages = await db.get_application_messages(application_id)

    # Форматируем информацию
    created_date = application["created_date"].strftime("%d.%m.%Y %H:%M")
    application_info = (
        f"📝 Заявка #{application_id}\n\n"
        f"👤 Пользователь: {application['first_name']} {application['last_name']} {application['middle_name']}\n"
        f"🏆 Олимпиада: {application['olympiad_title']}\n"
        f"🔄 Статус: {application['status_name']}\n"
        f"📅 Дата подачи: {created_date}"
    )

    if messages:
        application_info += "\n\n💬 Сообщение:"
        for i, msg in enumerate(messages, 1):
            application_info += f"\n{i}. {msg['first_name']} {msg['last_name']} ({msg['sent_date'].strftime('%d.%m.%Y %H:%M')}):\n{msg['message_text']}"

    if not messages:
        application_info += "\n\n💬 Сообщение: не найдено"

    await callback.message.answer(application_info, reply_markup=application_action_keyboard(application_id))
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("view_olympiad_"))
async def view_olympiad_details(callback: CallbackQuery):
    """Детальный просмотр олимпиады"""
    olympiad_id = int(callback.data.split("_")[2])
    olympiad = await db.get_olympiad_by_id(olympiad_id)

    if not olympiad:
        await callback.answer("Олимпиада не найдена")
        return

    # Получаем название дисциплины
    subject_name = await db.get_subject_name(olympiad["subject_id"])

    # Форматируем даты
    start_date = olympiad["start_date"].strftime("%d.%m.%Y")
    end_date = olympiad["end_date"].strftime("%d.%m.%Y")

    # Форматируем информацию
    olympiad_info = (
        f"🏆 <b>{olympiad['title']}</b>\n\n"
        f"📝 Описание: {olympiad['description']}\n"
        f"🏢 Организатор: {olympiad['organizer']}\n"
        f"📚 Дисциплина: {subject_name}\n"
        f"📅 Начало: {start_date}\n"
        f"📅 Окончание: {end_date}\n"
        f"🆔 ID: {olympiad['olympiad_id']}"
    )

    await callback.message.answer(olympiad_info, reply_markup=olympiad_detail_keyboard(olympiad_id), parse_mode="HTML")
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("change_app_status_"))
async def change_application_status(callback: CallbackQuery):
    """Изменение статуса заявки"""
    application_id = int(callback.data.split("_")[3])
    current_status = (await db.get_application_details(application_id))["status_name"]

    await callback.message.answer(
        "Выберите новый статус:", reply_markup=application_status_change_keyboard(application_id, current_status)
    )
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("set_app_status_"))
async def set_application_status(callback: CallbackQuery):
    """Установка нового статуса заявки"""
    parts = callback.data.split("_")
    application_id = int(parts[3])
    new_status = parts[4]

    success = await db.update_application_status(application_id, new_status)

    if success:
        await callback.message.answer(f"✅ Статус заявки изменен на '{new_status}'")
        # Здесь можно добавить уведомление пользователю
    else:
        await callback.message.answer("❌ Ошибка при изменении статуса")

    await callback.answer()


@router.callback_query(F.data.startswith("delete_app_"))
async def delete_application_admin(callback: CallbackQuery):
    """Удаление заявки администратором"""
    application_id = int(callback.data.split("_")[2])
    success = await db.delete_application(application_id)

    if success:
        await callback.message.answer("✅ Заявка успешно удалена")
    else:
        await callback.message.answer("❌ Ошибка при удалении заявки")

    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("edit_olympiad_"))
async def start_editing_olympiad(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования олимпиады"""
    olympiad_id = int(callback.data.split("_")[2])
    await state.update_data(olympiad_id=olympiad_id)

    await callback.message.answer("Выберите поле для редактирования:", reply_markup=edit_olympiad_field_keyboard())
    await state.set_state(EditOlympiadStates.select_field)
    await callback.message.delete()
    await callback.answer()


@router.callback_query(EditOlympiadStates.select_field, F.data.startswith("edit_field_"))
async def select_field_to_edit(callback: CallbackQuery, state: FSMContext):
    """Выбор поля для редактирования"""
    field = callback.data.split("_")[2]
    await state.update_data(edit_field=field)

    field_names = {
        "title": "название",
        "description": "описание",
        "organizer": "организатора",
        "start": "дату начала (в формате ГГГГ-ММ-ДД)",
        "end": "дату окончания (в формате ГГГГ-ММ-ДД)",
        # "subject": "дисциплину"
    }

    await callback.message.answer(f"Введите новое {field_names.get(field, 'значение')}:")

    # Устанавливаем соответствующее состояние
    if field == "title":
        await state.set_state(EditOlympiadStates.edit_title)
    elif field == "description":
        await state.set_state(EditOlympiadStates.edit_description)
    elif field == "organizer":
        await state.set_state(EditOlympiadStates.edit_organizer)
    elif field == "start_date":
        await state.set_state(EditOlympiadStates.edit_start_date)
    elif field == "end_date":
        await state.set_state(EditOlympiadStates.edit_end_date)
    elif field == "subject":
        await state.set_state(EditOlympiadStates.edit_subject)

    await callback.message.delete()
    await callback.answer()


@router.message(EditOlympiadStates.edit_title)
async def process_edit_title(message: Message, state: FSMContext):
    """Обработка нового названия"""
    data = await state.get_data()
    success = await db.update_olympiad_field(data["olympiad_id"], "title", message.text)
    await process_edit_complete(message, state, success, "название")


@router.message(EditOlympiadStates.edit_description)
async def process_edit_description(message: Message, state: FSMContext):
    """Обработка нового описания"""
    data = await state.get_data()
    success = await db.update_olympiad_field(data["olympiad_id"], "description", message.text)
    await process_edit_complete(message, state, success, "описание")


@router.message(EditOlympiadStates.edit_organizer)
async def process_edit_organizer(message: Message, state: FSMContext):
    """Обработка нового организатора"""
    data = await state.get_data()
    success = await db.update_olympiad_field(data["olympiad_id"], "organizer", message.text)
    await process_edit_complete(message, state, success, "организатора")


@router.message(EditOlympiadStates.edit_start_date)
async def process_edit_start_date(message: Message, state: FSMContext):
    """Обработка новой даты начала"""
    data = await state.get_data()
    success = await db.update_olympiad_field(data["olympiad_id"], "start_date", message.text)
    await process_edit_complete(message, state, success, "дату начала")


@router.message(EditOlympiadStates.edit_end_date)
async def process_edit_end_date(message: Message, state: FSMContext):
    """Обработка новой даты окончания"""
    data = await state.get_data()
    success = await db.update_olympiad_field(data["olympiad_id"], "end_date", message.text)
    await process_edit_complete(message, state, success, "дату окончания")


@router.message(EditOlympiadStates.edit_subject)
async def process_edit_subject(message: Message, state: FSMContext):
    """Обработка новой дисциплины"""
    data = await state.get_data()

    # Здесь должна быть логика поиска ID дисциплины по названию
    # Пока просто сохраняем название
    success = True  # Заглушка

    if success:
        await message.answer("✅ Дисциплина успешно обновлена")
    else:
        await message.answer("❌ Ошибка при обновлении дисциплины")

    await state.clear()
    await view_olympiad_details_by_id(message.bot, message.chat.id, data["olympiad_id"])


async def process_edit_complete(message: Message, state: FSMContext, success: bool, field_name: str):
    """Общая обработка завершения редактирования"""
    data = await state.get_data()

    if success:
        await message.answer(f"✅ {field_name.capitalize()} успешно обновлено")
    else:
        await message.answer(f"❌ Ошибка при обновлении {field_name}")

    await state.clear()
    await view_olympiad_details_by_id(message.bot, message.chat.id, data["olympiad_id"])


async def view_olympiad_details_by_id(bot, chat_id, olympiad_id):
    """Показывает детали олимпиады по ID (Вспомогательная при обработках)"""
    olympiad = await db.get_olympiad_by_id(olympiad_id)
    if not olympiad:
        await bot.send_message(chat_id, "Олимпиада не найдена")
        return

    subject_name = await db.get_subject_name(olympiad["subject_id"])
    start_date = olympiad["start_date"].strftime("%d.%m.%Y")
    end_date = olympiad["end_date"].strftime("%d.%m.%Y")
    olympiad_info = (
        f"🏆 <b>{olympiad['title']}</b>\n\n"
        f"📝 Описание: {olympiad['description']}\n"
        f"🏢 Организатор: {olympiad['organizer']}\n"
        f"📚 Дисциплина: {subject_name}\n"
        f"📅 Начало: {start_date}\n"
        f"📅 Окончание: {end_date}\n"
        f"🆔 ID: {olympiad['olympiad_id']}"
    )

    await bot.send_message(
        chat_id, olympiad_info, reply_markup=olympiad_detail_keyboard(olympiad_id), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("delete_olympiad_"))
async def delete_olympiad(callback: CallbackQuery):
    """Подтверждение удаления олимпиады"""
    olympiad_id = int(callback.data.split("_")[2])

    await callback.message.answer(
        "⚠️ Вы уверены, что хотите удалить эту олимпиаду? Все связанные заявки также будут удалены!",
        reply_markup=confirm_delete_keyboard("olympiad", olympiad_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_olympiad_"))
async def confirm_delete_olympiad(callback: CallbackQuery):
    """Обработка подтверждения удаления олимпиады"""
    if callback.data.startswith("confirm_delete_olympiad_no"):
        await callback.message.delete()
        await callback.answer("Удаление отменено")
        return
    olympiad_id = int(callback.data.split("_")[4])
    success = await db.delete_olympiad(olympiad_id)

    if success:
        await callback.message.answer("✅ Олимпиада успешно удалена")
    else:
        await callback.message.answer("❌ Ошибка при удалении олимпиады")

    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "back_to_admin_panel")
async def back_to_admin_panel(callback: CallbackQuery):
    """Возврат в админ-панель"""
    await callback.message.answer("👑 Панель администратора:", reply_markup=admin_main_keyboard())
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "back_to_olympiads_list")
async def back_to_olympiads_list(callback: CallbackQuery):
    """Возврат к списку олимпиад"""
    olympiads = await db.get_all_olympiads()
    await callback.message.answer("📋 Список всех олимпиад:", reply_markup=olympiads_list_keyboard(olympiads, page=0))
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_applications_list_"))
async def back_to_applications_list(callback: CallbackQuery):
    """Возврат к списку заявок на олимпиаду"""
    application_id = int(callback.data.split("_")[4])
    data_app = await db.get_application_details(application_id)
    applications = await db.get_applications_for_olympiad(data_app["olympiad_id"])

    if not applications:
        await callback.answer("На эту олимпиаду нет заявок")
        return

    olympiad = await db.get_olympiad_by_id(data_app["olympiad_id"])
    title = olympiad["title"] if olympiad else f"Олимпиада #{data_app['olympiad_id']}"

    await callback.message.answer(
        f"📋 Заявки на олимпиаду: {title}",
        reply_markup=olympiad_applications_keyboard(applications, data_app["olympiad_id"]),
    )
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "cancel_editing_olymp_field")
async def back_to_applications_list(callback: CallbackQuery):
    """Возврат к списку олимпиад"""
    await callback.message.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    if not await db.is_admin_or_moderator(callback.from_user.id):
        return

    olympiads = await db.get_all_olympiads()

    if not olympiads:
        await callback.message.answer("Список олимпиад пуст")
        return

    await callback.message.answer("📋 Список всех олимпиад:", reply_markup=olympiads_list_keyboard(olympiads, page=0))


@router.callback_query(F.data.startswith("export_olympiad_"))
async def export_olympiad_report(callback: CallbackQuery):
    """Генерация и отправка отчета по заявкам на олимпиаду"""
    olympiad_id = int(callback.data.split("_")[2])

    # Получаем информацию об олимпиаде
    olympiad = await db.get_full_olympiad_info(olympiad_id)
    if not olympiad:
        await callback.answer("Олимпиада не найдена")
        return

    # Получаем заявки на олимпиаду
    applications = await db.get_applications_for_olympiad(olympiad_id)

    # Генерируем отчет
    try:
        filename = generate_olympiad_report(olympiad, applications)

        # Создаем объект файла для отправки
        input_file = FSInputFile(filename)

        # Отправляем файл пользователю
        with open(filename, "rb") as file:
            await callback.message.answer_document(
                input_file, caption=f"Отчет по заявкам на олимпиаду: {olympiad['title']}"
            )

        # Удаляем временный файл
        os.remove(filename)
    except Exception as e:
        print(f"❌ Ошибка при генерации отчета: {e}")
        await callback.message.answer("❌ Произошла ошибка при генерации отчета")

    await callback.answer()


@router.callback_query(F.data.startswith("edit_app_message_"))
async def start_edit_application_message(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования сообщения для заявки"""
    application_id = int(callback.data.split("_")[3])

    # Получаем текущее сообщение модератора (если есть)
    messages = await db.get_application_messages(application_id)
    current_message = ""

    if messages:
        # Ищем сообщение текущего модератора
        for msg in messages:
            moderator = await db.get_user(msg["user_id"])
            if moderator and moderator["telegram_id"] == callback.from_user.id:
                current_message = msg["message_text"]
                break

    await state.update_data(application_id=application_id)

    if current_message:
        await callback.message.answer(
            f"Текущее сообщение: {current_message}\n\n"
            "Введите новое сообщение для заявки (или отправьте '-' чтобы удалить):"
        )
    else:
        await callback.message.answer("Введите сообщение для заявки (или отправьте '-' чтобы удалить):")

    await state.set_state(EditApplicationMessage.waiting_for_message)
    await callback.answer()


@router.message(EditApplicationMessage.waiting_for_message)
async def process_edit_application_message(message: Message, state: FSMContext):
    """Обработка нового сообщения для заявки"""
    data = await state.get_data()
    application_id = data["application_id"]

    # Получаем user_id модератора
    moderator = await db.get_user(message.from_user.id)
    if not moderator:
        await message.answer("❌ Ошибка: модератор не найден")
        await state.clear()
        return

    # Удаляем предыдущее сообщение этого модератора
    await db.delete_application_messages(application_id, moderator["user_id"])

    if message.text.strip() == "-":
        # Пользователь хочет удалить сообщение
        await message.answer("✅ Сообщение удалено!")
    else:
        # Сохраняем новое сообщение
        success = await db.create_message(
            user_id=moderator["user_id"], application_id=application_id, message_text=message.text
        )

        if success:
            await message.answer("✅ Сообщение успешно обновлено!")
        else:
            await message.answer("❌ Ошибка при обновлении сообщения")

    await state.clear()

    # Показываем обновленные детали заявки
    application = await db.get_application_details(application_id)
    messages = await db.get_application_messages(application_id)

    # Форматируем информацию
    created_date = application["created_date"].strftime("%d.%m.%Y %H:%M")
    application_info = (
        f"📝 Заявка #{application_id}\n\n"
        f"👤 Пользователь: {application['first_name']} {application['last_name']} {application['middle_name']}\n"
        f"🏆 Олимпиада: {application['olympiad_title']}\n"
        f"🔄 Статус: {application['status_name']}\n"
        f"📅 Дата подачи: {created_date}"
    )

    if messages:
        application_info += "\n\n💬 Сообщение:"
        for i, msg in enumerate(messages, 1):
            application_info += f"\n{i}. {msg['first_name']} {msg['last_name']} ({msg['sent_date'].strftime('%d.%m.%Y %H:%M')}):\n{msg['message_text']}"

    if not messages:
        application_info += "\n\n💬 Сообщение: не найдено"

    await message.answer(application_info, reply_markup=application_action_keyboard(application_id))
