import os
import asyncpg
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Загрузка конфигурации
TOKEN = os.getenv("TG__BOT_TOKEN")

# Проверка наличия токена
if not TOKEN:
    raise ValueError("TG__BOT_TOKEN не установлен в .env файле!")

# Инициализация бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Обработчик сообщений
@dp.message()
async def echo_handler(message: types.Message) -> None:
    await message.answer("Привет! Проверка связи...")

# Проверка подключения к бд
async def test_db_connection():
    print('Произвожу проверку подключения к базе данных: .... .')
    try:
        conn = await asyncpg.connect(
            host=os.getenv("DB__HOST"),
            port=os.getenv("DB__PORT"),
            user=os.getenv("DB__USER"),
            password=os.getenv("DB__PASSWORD"),
            database=os.getenv("DB__NAME")
        )
        version = await conn.fetchval("SELECT version()")
        print(f"✅ Подключение к PostgreSQL успешно! Версия: {version}")
        await conn.close()
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")

async def main() -> None:
    await test_db_connection()
    print("Бот запущен! Проверьте Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())