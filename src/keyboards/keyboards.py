from aiogram.utils.keyboard import InlineKeyboardBuilder
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

def confirm_delete_keyboard():
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
            callback_data=f"app_{app['application_id']}"
        )
    builder.adjust(1)
    return builder.as_markup()

def application_action_keyboard(application_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"app_approve_{application_id}")
    builder.button(text="❌ Отклонить", callback_data=f"app_reject_{application_id}")
    builder.button(text="↩️ Назад к списку", callback_data="back_to_applications")
    builder.adjust(2, 1)
    return builder.as_markup()

def reports_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Заявки по олимпиадам", callback_data="report_applications_by_olympiad")
    builder.button(text="🔄 Заявки по статусам", callback_data="report_applications_by_status")
    builder.button(text="👤 Участники по категориям", callback_data="report_users_by_category")
    builder.adjust(1)
    return builder.as_markup()