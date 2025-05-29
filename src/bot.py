import os
import asyncio
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from services.database import Database
from dispatcher import get_dispatcher

async def main():
    # Инициализация бота
    bot = Bot(
        token=os.getenv("TG__BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    # Инициализация диспетчера
    dp = get_dispatcher()
    
    # Инициализация бд
    db = Database()
    await db.initialize()
    
    # Запуск бота
    print("🤖 Бот запущен! Проверьте Telegram...")
    try:
        await dp.start_polling(bot)
    finally:
        # Гарантированное закрытие соединений
        await db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())