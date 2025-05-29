from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    await message.answer("👋 Привет! Я бот для регистрации на олимпиады.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    await message.answer("ℹ️ Помощь по боту:\n\n"
                         "/start - Начать работу\n"
                         "/help - Получить помощь\n"
                         "/status - Проверить статус системы")

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    """Обработчик команды /status"""
    await message.answer("🟢 Система работает нормально")
