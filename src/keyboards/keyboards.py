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

def main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📋 Мои заявки")
    builder.button(text="🏆 Доступные олимпиады")
    builder.button(text="📊 Мои результаты")
    builder.button(text="⚙️ Настройки")
    builder.button(text="ℹ️ Помощь")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)