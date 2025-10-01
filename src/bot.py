import asyncio
import os

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from dispatcher import get_dispatcher
from services.database import Database


async def main():
    # Инициализация базы данных
    db = Database()
    if not await db.initialize():
        print("❌ Не удалось инициализировать БД! Работа бота будет ограничена.")

    # Инициализация бота
    bot = Bot(token=os.getenv("TG__BOT_TOKEN"), default=DefaultBotProperties(parse_mode="HTML"))

    # Инициализация диспетчера
    dp = get_dispatcher()

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
