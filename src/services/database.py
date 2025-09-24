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
        
    async def get_category_name_by_user_id(self, user_id: int) -> str:
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
        
    async def get_category_name(self, category_id: int) -> str:
        """Получение названия категории по category_id"""
        if self.pool is None:
            if not await self.initialize():
                return 
        async with self.pool.acquire() as conn:
            category = await conn.fetchrow(
                "SELECT category_name FROM category WHERE category_id = $1",
                category_id
            )
            return category['category_name'] if category else "Не указана"

    async def delete_user(self, telegram_id: int) -> bool:
        """Удаление пользователя и связанных данных"""
        if self.pool is None:
            if not await self.initialize():
                return False
                
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Удаляем связанные данные из других таблиц
                    await conn.execute(
                        "DELETE FROM userrole WHERE user_id = (SELECT user_id FROM users WHERE telegram_id = $1)",
                        telegram_id
                    )

                    await conn.execute(
                        "DELETE FROM usercategory WHERE user_id = (SELECT user_id FROM users WHERE telegram_id = $1)",
                        telegram_id
                    )

                    await conn.execute(
                        "DELETE FROM messages WHERE application_id IN (SELECT application_id FROM application WHERE user_id = (SELECT user_id FROM users WHERE telegram_id = $1))",
                        telegram_id
                    )

                    await conn.execute(
                        "DELETE FROM application WHERE user_id = (SELECT user_id FROM users WHERE telegram_id = $1)",
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

    async def is_admin_or_moderator(self, telegram_id: int) -> bool:
        """Проверяет, является ли пользователь администратором или модератором"""
        if self.pool is None:
            if not await self.initialize():
                return False
                
        async with self.pool.acquire() as conn:
            user = await self.get_user(telegram_id)
            if not user:
                return False
                
            result = await conn.fetchval(
                """
                SELECT COUNT(*) 
                FROM UserRole ur
                JOIN Role r ON ur.role_id = r.role_id
                WHERE ur.user_id = $1 AND r.role_name IN ('Администратор', 'Модератор')
                """,
                user['user_id']
            )
            return result > 0
        
        # заявки на олимпиаду
    async def get_subjects(self):
        """Получение всех дисциплин"""
        if self.pool is None:
            if not await self.initialize():
                return []
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM Subject")

    async def get_subject_name(self, subject_id: int) -> str:
        """Получение названия дисциплины по ID"""
        if self.pool is None:
            if not await self.initialize():
                return "Неизвестная дисциплина"
        async with self.pool.acquire() as conn:
            subject = await conn.fetchrow(
                "SELECT title FROM Subject WHERE subject_id = $1",
                subject_id
            )
            return subject['title'] if subject else "Не указана"
        
    async def get_active_olympiads(self):
        """Получение активных олимпиад"""
        if self.pool is None:
            if not await self.initialize():
                return []
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM Olympiad WHERE end_date >= CURRENT_DATE"
            )
        
    async def create_olympiad(
        self,
        title: str,
        description: str,
        organizer: str,
        start_date: str,
        end_date: str,
        subject_id: int
    ) -> bool:
        """Создание новой олимпиады"""
        if self.pool is None:
            if not await self.initialize():
                return False
                
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO Olympiad 
                    (title, description, organizer, start_date, end_date, subject_id)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    title, description, organizer, start_date, end_date, subject_id
                )
                return True
            except Exception as e:
                print(f"Error creating olympiad: {e}")
                return False
            
    async def get_olympiad_by_id(self, olympiad_id: int):
        """Получение олимпиады по ID"""
        if self.pool is None:
            if not await self.initialize():
                return None
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM Olympiad WHERE olympiad_id = $1",
                olympiad_id
            )
            
    # Работа с application
    async def has_application(self, telegram_id: int, olympiad_id: int) -> bool:
        """Проверяет, есть ли у пользователя заявка на эту олимпиаду"""
        if self.pool is None:
            if not await self.initialize():
                return False
        async with self.pool.acquire() as conn:
            user = await self.get_user(telegram_id)
            if not user:
                return False
                
            count = await conn.fetchval(
                """
                SELECT COUNT(*) 
                FROM Application 
                WHERE user_id = $1 AND olympiad_id = $2
                """,
                user['user_id'], olympiad_id
            )
            return count > 0
        
    async def create_application(self, telegram_id: int, olympiad_id: int) -> bool:
        """Создание новой заявки"""
        if self.pool is None:
            if not await self.initialize():
                return False
                
        async with self.pool.acquire() as conn:
            try:
                user = await self.get_user(telegram_id)
                if not user:
                    return False
                    
                # Статус "Рассмотрение" - ожидает подтверждения
                status_id = await conn.fetchval(
                    "SELECT status_id FROM ApplicationStatus WHERE status_name = 'Рассмотрение'"
                )
                
                await conn.execute(
                    """
                    INSERT INTO Application 
                    (olympiad_id, user_id, status_id)
                    VALUES ($1, $2, $3)
                    """,
                    olympiad_id, user['user_id'], status_id
                )
                return True
            except Exception as e:
                print(f"Ошибка создания заявки на олимпиаду: {e}")
                return False
            
    async def get_pending_applications(self):
        """Получение заявок, ожидающих модерации"""
        if self.pool is None:
            if not await self.initialize():
                return []
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """
                SELECT a.application_id, u.first_name, u.last_name, o.title AS olympiad_title
                FROM Application a
                JOIN Users u ON a.user_id = u.user_id
                JOIN Olympiad o ON a.olympiad_id = o.olympiad_id
                JOIN ApplicationStatus s ON a.status_id = s.status_id
                WHERE s.status_name = 'Рассмотрение'
                """
            )

    async def get_application_details(self, application_id: int):
        """Получение детальной информации о заявке"""
        if self.pool is None:
            if not await self.initialize():
                return None
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT 
                    a.application_id,
                    u.first_name,
                    u.last_name,
                    o.title AS olympiad_title,
                    s.status_name,
                    a.created_date
                FROM Application a
                JOIN Users u ON a.user_id = u.user_id
                JOIN Olympiad o ON a.olympiad_id = o.olympiad_id
                JOIN ApplicationStatus s ON a.status_id = s.status_id
                WHERE a.application_id = $1
                """,
                application_id
            )

    async def update_application_status(self, application_id: int, status_name: str) -> bool:
        """Обновление статуса заявки"""
        if self.pool is None:
            if not await self.initialize():
                return False
                
        async with self.pool.acquire() as conn:
            try:
                status_id = await conn.fetchval(
                    "SELECT status_id FROM ApplicationStatus WHERE status_name = $1",
                    status_name
                )
                
                if not status_id:
                    return False
                    
                await conn.execute(
                    "UPDATE Application SET status_id = $1 WHERE application_id = $2",
                    status_id, application_id
                )
                return True
            except Exception as e:
                print(f"Error updating application status: {e}")
                return False
            
    async def get_all_olympiads(self):
        """Получение всех олимпиад"""
        if self.pool is None:
            if not await self.initialize():
                return []
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM Olympiad ORDER BY start_date DESC"
            )

    async def get_olympiad_by_id(self, olympiad_id: int):
        """Получение олимпиады по ID"""
        if self.pool is None:
            if not await self.initialize():
                return None
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM Olympiad WHERE olympiad_id = $1",
                olympiad_id
            )

    async def get_subject_name(self, subject_id: int) -> str:
        """Получение названия дисциплины по ID"""
        if self.pool is None:
            if not await self.initialize():
                return "Неизвестная дисциплина"
        async with self.pool.acquire() as conn:
            subject = await conn.fetchrow(
                "SELECT title FROM Subject WHERE subject_id = $1",
                subject_id
            )
            return subject['title'] if subject else "Не указана"

    async def get_applications_for_olympiad(self, olympiad_id: int):
        """Получение всех заявок для олимпиады"""
        if self.pool is None:
            if not await self.initialize():
                return []
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """
                SELECT 
                    a.application_id,
                    u.first_name,
                    u.last_name,
                    u.middle_name,
                    s.status_name,
                    a.created_date
                FROM Application a
                JOIN Users u ON a.user_id = u.user_id
                JOIN ApplicationStatus s ON a.status_id = s.status_id
                WHERE a.olympiad_id = $1
                ORDER BY a.created_date DESC
                """,
                olympiad_id
            )

    async def get_application_details(self, application_id: int):
        """Получение детальной информации о заявке"""
        if self.pool is None:
            if not await self.initialize():
                return None
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT 
                    u.user_id,
                    a.olympiad_id,
                    a.application_id,
                    u.first_name,
                    u.last_name,
                    u.middle_name,
                    o.title AS olympiad_title,
                    s.status_name,
                    a.created_date
                FROM Application a
                JOIN Users u ON a.user_id = u.user_id
                JOIN Olympiad o ON a.olympiad_id = o.olympiad_id
                JOIN ApplicationStatus s ON a.status_id = s.status_id
                WHERE a.application_id = $1
                """,
                application_id
            )

    async def update_application_status(self, application_id: int, status_name: str) -> bool:
        """Обновление статуса заявки"""
        if self.pool is None:
            if not await self.initialize():
                return False
                
        async with self.pool.acquire() as conn:
            try:
                status_id = await conn.fetchval(
                    "SELECT status_id FROM ApplicationStatus WHERE status_name = $1",
                    status_name
                )
                
                if not status_id:
                    return False
                    
                await conn.execute(
                    "UPDATE Application SET status_id = $1 WHERE application_id = $2",
                    status_id, application_id
                )
                return True
            except Exception as e:
                print(f"Error updating application status: {e}")
                return False

    async def delete_application(self, application_id: int) -> bool:
        """Удаление заявки по ID"""
        if self.pool is None:
            if not await self.initialize():
                return False
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "DELETE FROM Messages WHERE application_id = $1",
                    application_id
                )
                result = await conn.execute(
                    "DELETE FROM Application WHERE application_id = $1",
                    application_id
                )
            return "DELETE 1" in result

    async def update_olympiad_field(self, olympiad_id: int, field: str, value: str) -> bool:
        """Обновление поля олимпиады"""
        if self.pool is None:
            if not await self.initialize():
                return False
                
        async with self.pool.acquire() as conn:
            try:
                # Для дат нужно преобразование
                if field in ['start_date', 'end_date']:
                    # Предполагаем, что value в формате ГГГГ-ММ-ДД
                    await conn.execute(
                        f"UPDATE Olympiad SET {field} = $1::date WHERE olympiad_id = $2",
                        value, olympiad_id
                    )
                else:
                    await conn.execute(
                        f"UPDATE Olympiad SET {field} = $1 WHERE olympiad_id = $2",
                        value, olympiad_id
                    )
                return True
            except Exception as e:
                print(f"Error updating olympiad field: {e}")
                return False

    async def delete_olympiad(self, olympiad_id: int) -> bool:
        """Удаление олимпиады и связанных данных"""
        if self.pool is None:
            if not await self.initialize():
                return False
        try:    
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Удаляем связанные сообщения
                    await conn.execute(
                        "DELETE FROM messages m USING Application a WHERE m.application_id = a.application_id AND a.olympiad_id = $1",
                        olympiad_id
                    )

                    # Удаляем связанные заявки
                    await conn.execute(
                        "DELETE FROM Application WHERE olympiad_id = $1",
                        olympiad_id
                    )
                    
                    # Удаляем олимпиаду
                    result = await conn.execute(
                        "DELETE FROM Olympiad WHERE olympiad_id = $1",
                        olympiad_id
                    )
                    
                    # Если удалена хотя бы одна строка - успех
                    return "DELETE 1" in result
        except Exception as e:
            print(f"❌ Ошибка при удалении олимпиады: {e}")
            return False
            
    async def get_full_olympiad_info(self, olympiad_id: int):
        """Получение полной информации об олимпиаде с названием дисциплины"""
        if self.pool is None:
            if not await self.initialize():
                return None
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT 
                    o.*,
                    s.title AS subject_title
                FROM Olympiad o
                JOIN Subject s ON o.subject_id = s.subject_id
                WHERE o.olympiad_id = $1
                """,
                olympiad_id
            )
    
    async def update_user_profile(self, telegram_id: int, **kwargs):
        """Обновление профиля пользователя"""
        if self.pool is None:
            if not await self.initialize():
                return False
                
        async with self.pool.acquire() as conn:
            try:
                user = await self.get_user(telegram_id)
                if not user:
                    return False
                    
                # Обновление основных данных пользователя
                basic_fields = ['first_name', 'last_name', 'middle_name']
                basic_updates = {k: v for k, v in kwargs.items() if k in basic_fields}
                
                if basic_updates:
                    set_clauses = []
                    values = []
                    for key, value in basic_updates.items():
                        set_clauses.append(f"{key} = ${len(set_clauses)+1}")
                        values.append(value)
                    
                    query = f"""
                        UPDATE Users
                        SET {", ".join(set_clauses)}
                        WHERE user_id = ${len(set_clauses)+1}
                    """
                    values.append(user['user_id'])
                    await conn.execute(query, *values)
                
                # Обновление категории
                if 'category_id' in kwargs:
                    category_id = kwargs['category_id']
                    await conn.execute(
                        "UPDATE UserCategory SET category_id = $1 WHERE user_id = $2",
                        category_id, user['user_id']
                    )

                return True
            except Exception as e:
                print(f"Error updating user profile: {e}")
                return False

    async def get_categories(self):
        """Получение всех категорий"""
        if self.pool is None:
            if not await self.initialize():
                return []
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM Category ORDER BY category_name")
        
    # Сообщения для заявок
    async def create_message(
        self,
        user_id: int,
        application_id: int,
        message_text: str
    ) -> bool:
        """Создание нового сообщения по заявке"""
        if self.pool is None:
            if not await self.initialize():
                return False
                
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO Messages (user_id, application_id, message_text)
                    VALUES ($1, $2, $3)
                    """,
                    user_id, application_id, message_text
                )
                return True
            except Exception as e:
                print(f"Error creating message: {e}")
                return False
            
    async def get_application_messages(self, application_id: int):
        """Получение сообщения по заявке"""
        if self.pool is None:
            if not await self.initialize():
                return []
                
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """
                SELECT m.*, u.first_name, u.last_name 
                FROM Messages m
                JOIN Users u ON m.user_id = u.user_id
                WHERE application_id = $1
                ORDER BY sent_date DESC
                """,
                application_id
            )
    async def delete_application_messages(self, application_id: int, user_id: int) -> bool:
        """Удаляет все сообщения по заявке от конкретного пользователя"""
        if self.pool is None:
            if not await self.initialize():
                return False
                
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    "DELETE FROM Messages WHERE application_id = $1 AND user_id = $2",
                    application_id, user_id
                )
                return True
            except Exception as e:
                print(f"Error deleting messages: {e}")
                return False


    async def get_user_applications(self, user_id: int):
        """Получение заявок пользователя"""
        if self.pool is None:
            if not await self.initialize():
                return []
                
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """
                SELECT 
                    a.application_id,
                    o.title AS olympiad_title,
                    s.status_name,
                    a.created_date
                FROM Application a
                JOIN Olympiad o ON a.olympiad_id = o.olympiad_id
                JOIN ApplicationStatus s ON a.status_id = s.status_id
                WHERE a.user_id = $1
                ORDER BY a.created_date DESC
                """,
                user_id
            )

    async def get_application_moderator_message(self, application_id: int):
        """Получение сообщения модератора для заявки"""
        if self.pool is None:
            if not await self.initialize():
                return None
                
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT m.message_text
                FROM Messages m
                JOIN Users u ON m.user_id = u.user_id
                JOIN UserRole ur ON ur.user_id = u.user_id
                JOIN Role r ON r.role_id = ur.role_id
                WHERE m.application_id = $1 
                AND r.role_name IN ('Модератор', 'Администратор')
                ORDER BY m.sent_date DESC
                LIMIT 1
                """,
                application_id
            )