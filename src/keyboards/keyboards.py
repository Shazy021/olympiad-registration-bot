from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, всё верно", callback_data="confirm_yes")
    builder.button(text="❌ Нет, начать заново", callback_data="confirm_no")
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

def main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 Профиль")  # Новая кнопка
    builder.button(text="📋 Мои заявки")
    builder.button(text="🏆 Доступные олимпиады")
    builder.button(text="📊 Мои результаты")
    builder.button(text="⚙️ Настройки")
    builder.button(text="ℹ️ Помощь")
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
