import asyncpg
import os

class Database:
    def __init__(self):
        self.pool = None
        
    async def initialize(self):
        """Инициализация пула подключений к БД"""
        try:
            self.pool = await asyncpg.create_pool(
                host=os.getenv("DB__HOST", "db"),
                port=int(os.getenv("DB__PORT", 5432)),
                user=os.getenv("DB__USER"),
                password=os.getenv("DB__PASSWORD"),
                database=os.getenv("DB__NAME"),
                min_size=1,
                max_size=10
            )
            print("✅ Подключение к PostgreSQL успешно установлено!")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к PostgreSQL: {e}")
            return False
        
    async def close(self):
        """Закрытие пула подключений"""
        if self.pool:
            await self.pool.close()
            print("🔌 Соединение с БД закрыто")