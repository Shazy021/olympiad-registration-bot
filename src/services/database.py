import asyncpg
import os
from typing import Optional

class Database:
    _instance = None
    
    def __new__(cls):
        """Реализация Singleton паттерна"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pool = None
        return cls._instance

    async def initialize(self):
        """Инициализация пула подключений к БД"""
        if self.pool is not None:
            return True
            
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
            self.pool = None

    async def get_user(self, telegram_id: int) -> Optional[asyncpg.Record]:
        """Получение пользователя по Telegram ID"""
        if self.pool is None:
            if not await self.initialize():
                return None
                
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1", 
                telegram_id
            )

    async def create_user(
        self,
        telegram_id: int,
        first_name: str,
        last_name: str,
        middle_name: Optional[str] = None,
        role: str = "Студент"
    ) -> None:
        """Создание нового пользователя"""
        if self.pool is None:
            if not await self.initialize():
                return
                
        async with self.pool.acquire() as conn:
            # Сохраняем пользователя
            user_id = await conn.fetchval(
                """
                INSERT INTO users (telegram_id, first_name, last_name, middle_name)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (telegram_id) DO NOTHING
                RETURNING user_id
                """,
                telegram_id, first_name, last_name, middle_name
            )
            
            # Если пользователь создан, добавляем роль
            if user_id:
                # Получаем ID роли по названию
                role_id = await conn.fetchval(
                    "SELECT role_id FROM role WHERE role_name = $1",
                    role.capitalize()
                )
                
                if role_id:
                    await conn.execute(
                        "INSERT INTO UserRole (user_id, role_id) VALUES ($1, $2)",
                        user_id, role_id
                    )
                    