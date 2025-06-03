from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, всё верно", callback_data="confirm_yes")
    builder.button(text="❌ Нет, начать заново", callback_data="confirm_no")
    builder.adjust(1)
    return builder.as_markup()

def confirm_olimp_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подать заявление", callback_data="application_confirm")
    builder.adjust(1)
    return builder.as_markup()

def role_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎓 Студент", callback_data="role_student")
    builder.button(text="👨‍🏫 Преподаватель", callback_data="role_teacher")
    builder.button(text="👑 Администратор", callback_data="role_admin")
    builder.adjust(1)
    return builder.as_markup()

def categories_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎓 Школьник", callback_data="category_1")
    builder.button(text="👨‍🎓 Студент", callback_data="category_2")
    builder.button(text="👨‍💼 Аспирант", callback_data="category_3")
    builder.button(text="👨‍🏫 Преподаватель", callback_data="category_4")
    builder.adjust(2, 2)
    return builder.as_markup()

def main_menu_keyboard(is_admin=False):
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 Профиль")
    builder.button(text="📋 Мои заявки")
    builder.button(text="🏆 Доступные олимпиады")
    builder.button(text="📊 Мои результаты")
    builder.button(text="⚙️ Настройки")
    builder.button(text="ℹ️ Помощь")
    if is_admin:
        builder.button(text="👑 Админ-панель")
        builder.adjust(1, 2, 2, 1, 1)
    else:
        builder.adjust(1, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def settings_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="✏️ Изменить профиль")
    builder.button(text="🔔 Уведомления")
    builder.button(text="❌ Удалить аккаунт")
    builder.button(text="🏠 Главное меню")
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def confirm_delete_keyboard_del_acc():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data="delete_yes")
    builder.button(text="❌ Нет, отменить", callback_data="delete_no")
    builder.adjust(2)
    return builder.as_markup()

def admin_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Добавить олимпиаду")
    builder.button(text="📋 Список олимпиад")
    builder.button(text="📝 Заявки на модерации")
    builder.button(text="📊 Отчеты")
    builder.button(text="🏠 Главное меню")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def subjects_keyboard(subjects):
    builder = InlineKeyboardBuilder()
    for subject in subjects:
        builder.button(
            text=subject['title'],
            callback_data=f"subject_{subject['subject_id']}"
        )
    builder.adjust(1)
    return builder.as_markup()

def back_to_admin_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="👑 Админ-панель")
    return builder.as_markup(resize_keyboard=True)

def olympiads_keyboard(olympiads):
    builder = InlineKeyboardBuilder()
    for olympiad in olympiads:
        builder.button(
            text=olympiad['title'],
            callback_data=f"olympiad_{olympiad['olympiad_id']}"
        )
    builder.adjust(1)
    return builder.as_markup()

def application_list_keyboard(applications):
    builder = InlineKeyboardBuilder()
    for app in applications:
        builder.button(
            text=f"Заявка #{app['application_id']} - {app['first_name']} {app['last_name']}",
            callback_data=f"app_id_{app['application_id']}"
        )
    builder.adjust(1)
    return builder.as_markup()

def moder_application_action_keyboard(application_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"app_approve_{application_id}")
    builder.button(text="❌ Отклонить", callback_data=f"app_reject_{application_id}")
    builder.button(text="↩️ Назад к списку", callback_data="back_to_applications_moderation")
    builder.adjust(2, 1)
    return builder.as_markup()

def reports_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Заявки по олимпиадам", callback_data="report_applications_by_olympiad")
    builder.button(text="🔄 Заявки по статусам", callback_data="report_applications_by_status")
    builder.button(text="👤 Участники по категориям", callback_data="report_users_by_category")
    builder.adjust(1)
    return builder.as_markup()

def olympiads_list_keyboard(olympiads, page=0, per_page=5):
    """Клавиатура списка олимпиад с пагинацией"""
    builder = InlineKeyboardBuilder()
    
    # Рассчитываем индексы для текущей страницы
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(olympiads))
    
    # Добавляем кнопки для олимпиад на текущей странице
    for olympiad in olympiads[start_idx:end_idx]:
        builder.button(
            text=f"{olympiad['title']} ({olympiad['start_date'].strftime('%d.%m.%Y')})",
            callback_data=f"view_olympiad_{olympiad['olympiad_id']}"
        )
    
    # Добавляем кнопки пагинации
    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(
            text="⬅️ Назад", 
            callback_data=f"olympiads_page_{page-1}"
        ))
    
    if end_idx < len(olympiads):
        pagination_row.append(InlineKeyboardButton(
            text="Вперед ➡️", 
            callback_data=f"olympiads_page_{page+1}"
        ))
    
    if pagination_row:
        builder.row(*pagination_row)
    
    # Кнопка возврата
    builder.button(text="🔙 В админ-панель", callback_data="back_to_admin_panel")
    builder.adjust(1)
    return builder.as_markup()

def olympiad_detail_keyboard(olympiad_id):
    """Клавиатура для детального просмотра олимпиады"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"edit_olympiad_{olympiad_id}")
    builder.button(text="🗑️ Удалить", callback_data=f"delete_olympiad_{olympiad_id}")
    builder.button(text="📋 Заявки", callback_data=f"view_olympiad_apps_{olympiad_id}")
    builder.button(text="🔙 К списку", callback_data="back_to_olympiads_list")
    builder.adjust(2, 2)
    return builder.as_markup()

def olympiad_applications_keyboard(applications, olympiad_id):
    """Клавиатура заявок на конкретную олимпиаду"""
    builder = InlineKeyboardBuilder()
    for app in applications:
        status_icon = "🟡" if app['status_name'] == 'pending' else "🟢" if app['status_name'] == 'approved' else "🔴"
        builder.button(
            text=f"{status_icon} {app['first_name']} {app['last_name']} - {app['status_name']}",
            callback_data=f"app_admin_app_check_{app['application_id']}"
        )
    
    builder.button(text="🔙 К олимпиаде", callback_data=f"view_olympiad_{olympiad_id}")
    builder.adjust(1)
    return builder.as_markup()

def application_action_keyboard(application_id):
    """Клавиатура действий с заявкой для администратора"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить статус", callback_data=f"change_app_status_{application_id}")
    builder.button(text="🗑️ Удалить заявку", callback_data=f"delete_app_{application_id}")
    builder.button(text="🔙 Назад", callback_data=f"back_to_applications_list_{application_id}")
    builder.adjust(2, 1)
    return builder.as_markup()

def application_status_change_keyboard(application_id, current_status):
    """Клавиатура изменения статуса заявки"""
    builder = InlineKeyboardBuilder()
    
    statuses = ["Рассмотрение", "approved", "rejected"]
    for status in statuses:
        if status != current_status:
            builder.button(
                text=status.capitalize(),
                callback_data=f"set_app_status_{application_id}_{status}"
            )
    
    builder.button(text="🔙 Назад", callback_data=f"app_admin_app_check_{application_id}")
    builder.adjust(1)
    return builder.as_markup()

def edit_olympiad_field_keyboard():
    """Клавиатура выбора поля для редактирования олимпиады"""
    builder = InlineKeyboardBuilder()
    builder.button(text="Название", callback_data="edit_field_title")
    builder.button(text="Описание", callback_data="edit_field_description")
    builder.button(text="Организатор", callback_data="edit_field_organizer")
    builder.button(text="Дата начала", callback_data="edit_field_start_date")
    builder.button(text="Дата окончания", callback_data="edit_field_end_date")
    # builder.button(text="Дисциплина", callback_data="edit_field_subject") Нужно будет продумать позже
    builder.button(text="Отменить редактирование", callback_data="cancel_editing_olymp_field")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def confirm_delete_keyboard(entity_type, entity_id):
    """Универсальная клавиатура подтверждения удаления"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Да, удалить", 
        callback_data=f"confirm_delete_{entity_type}_yes_{entity_id}"
    )
    builder.button(
        text="❌ Нет, отменить", 
        callback_data=f"confirm_delete_{entity_type}_no"
    )
    builder.adjust(2)
    return builder.as_markup()
