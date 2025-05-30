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
        role: str = "Студент",
        category_id: Optional[int] = None
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
                    role
                )
                
                if role_id:
                    await conn.execute(
                        "INSERT INTO UserRole (user_id, role_id) VALUES ($1, $2)",
                        user_id, role_id
                    )
                if category_id:
                    await conn.execute(
                        "INSERT INTO UserCategory (user_id, category_id) VALUES ($1, $2)",
                        user_id, category_id
                    )

    async def get_role_name(self, user_id: int) -> str:
        """Получение названия роли по user_id"""
        if self.pool is None:
            if not await self.initialize():
                return 
        async with self.pool.acquire() as conn:
            category = await conn.fetchrow(
                "SELECT role_name FROM role WHERE role_id = (SELECT role_id FROM UserRole WHERE user_id = $1)",
                user_id
            )
            return category['role_name'] if category else "Не указана"
        
    async def get_category_name(self, user_id: int) -> str:
        """Получение названия категории по user_id"""
        if self.pool is None:
            if not await self.initialize():
                return 
        async with self.pool.acquire() as conn:
            category = await conn.fetchrow(
                "SELECT category_name FROM category WHERE category_id = (SELECT category_id FROM UserCategory WHERE user_id = $1)",
                user_id
            )
            return category['category_name'] if category else "Не указана"

    async def delete_user(self, telegram_id: int) -> bool:
        """Удаление пользователя и связанных данных"""
        if self.pool is None:
            if not await self.initialize():
                return False
                
        try:
            async with self.pool.acquire() as conn:
                # Удаляем связанные данные из других таблиц
                await conn.execute(
                    "DELETE FROM userrole WHERE user_id = (SELECT user_id FROM users WHERE telegram_id = $1)",
                    telegram_id
                )
                
                # Удаляем пользователя
                result = await conn.execute(
                    "DELETE FROM users WHERE telegram_id = $1",
                    telegram_id
                )
                
                # Если удалена хотя бы одна строка - успех
                return "DELETE 1" in result
        except Exception as e:
            print(f"❌ Ошибка при удалении пользователя: {e}")
            return False
