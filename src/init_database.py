import asyncio
import os
from datetime import date, datetime

import asyncpg


async def create_tables_and_seed():
    """Создание таблиц и заполнение БД с нуля"""

    # Подключение к БД
    try:
        conn = await asyncpg.connect(
            host=os.getenv("DB__HOST", "db"),
            port=int(os.getenv("DB__PORT", "5432")),
            user=os.getenv("DB__USER", "admin"),
            password=os.getenv("DB__PASSWORD"),
            database=os.getenv("DB__NAME"),
        )
        print("✅ Подключились к PostgreSQL")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return

    try:
        print("🗄️ Создаем структуру БД...")

        # ========== СОЗДАНИЕ ТАБЛИЦ ==========

        # Справочные таблицы
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Role (
                role_id SERIAL PRIMARY KEY,
                role_name VARCHAR(50) NOT NULL UNIQUE
            );
        """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Category (
                category_id SERIAL PRIMARY KEY,
                category_name VARCHAR(50) NOT NULL UNIQUE
            );
        """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ApplicationStatus (
                status_id SERIAL PRIMARY KEY,
                status_name VARCHAR(50) NOT NULL UNIQUE
            );
        """
        )

        # Основная таблица пользователей
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Users (
                user_id SERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL UNIQUE,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100),
                middle_name VARCHAR(100)
            );
        """
        )

        # Таблица дисциплин
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Subject (
                subject_id SERIAL PRIMARY KEY,
                title VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                code VARCHAR(20) UNIQUE
            );
        """
        )

        # Таблица олимпиад
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Olympiad (
                olympiad_id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                organizer VARCHAR(150),
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                subject_id INT NOT NULL REFERENCES Subject(subject_id) ON DELETE CASCADE
            );
        """
        )

        # Связующие таблицы
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS UserRole (
                user_role_id SERIAL PRIMARY KEY,
                user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
                role_id INT NOT NULL REFERENCES Role(role_id) ON DELETE RESTRICT,
                CONSTRAINT unique_user_role UNIQUE (user_id, role_id)
            );
        """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS UserCategory (
                user_category_id SERIAL PRIMARY KEY,
                user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
                category_id INT NOT NULL REFERENCES Category(category_id) ON DELETE RESTRICT,
                CONSTRAINT unique_user_category UNIQUE (user_id, category_id)
            );
        """
        )

        # Таблица заявок
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Application (
                application_id SERIAL PRIMARY KEY,
                olympiad_id INT NOT NULL REFERENCES Olympiad(olympiad_id) ON DELETE CASCADE,
                user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
                status_id INT NOT NULL REFERENCES ApplicationStatus(status_id) ON DELETE RESTRICT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )

        # Таблица сообщений
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Messages (
                message_id SERIAL PRIMARY KEY,
                user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
                application_id INT NOT NULL REFERENCES Application(application_id) ON DELETE CASCADE,
                message_text TEXT NOT NULL,
                sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )

        print("✅ Таблицы созданы успешно!")

        # ========== ЗАПОЛНЕНИЕ ДАННЫМИ ==========

        print("📚 Заполняем справочники...")

        # Очистка и заполнение справочников
        await conn.execute(
            "TRUNCATE TABLE Messages, Application, UserCategory, UserRole, Olympiad, Users, Subject, ApplicationStatus, Category, Role RESTART IDENTITY CASCADE;"
        )

        # Роли
        await conn.executemany(
            "INSERT INTO Role (role_name) VALUES ($1)", [("Студент",), ("Модератор",), ("Администратор",)]
        )

        # Категории
        await conn.executemany(
            "INSERT INTO Category (category_name) VALUES ($1)",
            [("Школьник",), ("Студент",), ("Аспирант",), ("Преподаватель",)],
        )

        # Статусы заявок
        await conn.executemany(
            "INSERT INTO ApplicationStatus (status_name) VALUES ($1)",
            [("Рассмотрение",), ("Одобрена",), ("Отклонена",)],
        )

        # Дисциплины
        subjects_data = [
            ("Математика", "Олимпиады по математике различного уровня", "MATH"),
            ("Физика", "Олимпиады по физике и астрономии", "PHYS"),
            ("Химия", "Химические олимпиады и конкурсы", "CHEM"),
            ("Информатика", "Олимпиады по информатике и программированию", "INFO"),
            ("Программирование", "Конкурсы по программированию и алгоритмам", "PROG"),
        ]
        await conn.executemany("INSERT INTO Subject (title, description, code) VALUES ($1, $2, $3)", subjects_data)

        print("👥 Создаем пользователей...")

        # Пользователи с тестовыми Telegram ID
        users_data = [
            (123456789, "Админ", "Системный", "Главный"),  # ID=1, Администратор
            (987654321, "Модератор", "Тестовый", "Иванович"),  # ID=2, Модератор
            (111111111, "Иван", "Петров", "Сергеевич"),  # ID=3, Студент
            (222222222, "Мария", "Сидорова", "Александровна"),  # ID=4, Студент
            (333333333, "Алексей", "Козлов", None),  # ID=5, Студент
            (444444444, "Елена", "Волкова", "Дмитриевна"),  # ID=6, Студент
            (555555555, "Дмитрий", "Лебедев", "Андреевич"),  # ID=7, Студент
            (666666666, "Анна", "Морозова", "Викторовна"),  # ID=8, Студент
        ]
        await conn.executemany(
            "INSERT INTO Users (telegram_id, first_name, last_name, middle_name) VALUES ($1, $2, $3, $4)", users_data
        )

        # Назначение ролей (user_id, role_id)
        roles_data = [
            (1, 3),  # Админ -> Администратор
            (2, 2),  # Модератор -> Модератор
            (3, 1),
            (4, 1),
            (5, 1),
            (6, 1),
            (7, 1),
            (8, 1),  # Остальные -> Студент
        ]
        await conn.executemany("INSERT INTO UserRole (user_id, role_id) VALUES ($1, $2)", roles_data)

        # Назначение категорий (user_id, category_id)
        categories_data = [
            (1, 4),
            (2, 4),  # Админ и Модератор -> Преподаватель
            (3, 2),
            (4, 2),
            (5, 2),  # Иван, Мария, Алексей -> Студент
            (6, 1),  # Елена -> Школьник
            (7, 3),  # Дмитрий -> Аспирант
            (8, 4),  # Анна -> Преподаватель
        ]
        await conn.executemany("INSERT INTO UserCategory (user_id, category_id) VALUES ($1, $2)", categories_data)

        print("🏆 Создаем олимпиады...")

        # Олимпиады (включая активные на июнь 2025)
        olympiads_data = [
            # АКТИВНЫЕ НА ИЮНЬ 2025 (для тестирования)
            (
                "Летняя олимпиада по математике",
                "Летний тур математической олимпиады для студентов. Включает задачи по всем разделам высшей математики.",
                "Летняя школа МГУ",
                date(2025, 6, 1),
                date(2025, 6, 30),
                1,
            ),
            (
                'Программистский марафон "Лето Кода"',
                "Интенсивное соревнование по программированию. Задачи по алгоритмам, структурам данных и олимпиадному программированию.",
                "Яндекс",
                date(2025, 6, 5),
                date(2025, 6, 20),
                5,
            ),
            (
                "Весенне-летняя физическая олимпиада",
                "Олимпиада по физике с акцентом на экспериментальные задачи и практические применения.",
                "МФТИ Летняя школа",
                date(2025, 5, 25),
                date(2025, 6, 15),
                2,
            ),
            (
                'Химический турнир "Начало лета"',
                "Практическая олимпиада по химии с лабораторными работами и синтезом веществ.",
                "ХимФак МГУ",
                date(2025, 6, 8),
                date(2025, 6, 25),
                3,
            ),
            (
                'IT-хакатон "Цифровое лето"',
                "Командный хакатон по разработке мобильных приложений и веб-сервисов.",
                "Mail.ru Group",
                date(2025, 6, 10),
                date(2025, 6, 12),
                4,
            ),
            # БУДУЩИЕ ОЛИМПИАДЫ
            (
                "Математическая олимпиада МГУ 2025",
                "Международная олимпиада по математике для студентов высших учебных заведений.",
                "МГУ им. М.В. Ломоносова",
                date(2025, 9, 15),
                date(2025, 11, 30),
                1,
            ),
            (
                "Физическая олимпиада МФТИ",
                "Всероссийская олимпиада по физике с международным участием.",
                "МФТИ",
                date(2025, 10, 1),
                date(2025, 12, 15),
                2,
            ),
            (
                "Химическая олимпиада СПбГУ",
                "Олимпиада по общей, неорганической, органической и физической химии.",
                "СПбГУ",
                date(2025, 10, 15),
                date(2025, 12, 20),
                3,
            ),
        ]
        await conn.executemany(
            "INSERT INTO Olympiad (title, description, organizer, start_date, end_date, subject_id) VALUES ($1, $2, $3, $4, $5, $6)",
            olympiads_data,
        )

        print("📋 Создаем тестовые заявки...")

        # Тестовые заявки на активные олимпиады
        applications_data = [
            # ===== ЛЕТНЯЯ ОЛИМПИАДА ПО МАТЕМАТИКЕ (ID=1) =====
            (1, 3, 2, datetime(2025, 6, 2, 10, 0)),  # Иван, одобрена
            (1, 4, 1, datetime(2025, 6, 3, 14, 30)),  # Мария, на рассмотрении
            (1, 6, 3, datetime(2025, 6, 4, 9, 15)),  # Елена, отклонена
            (1, 8, 2, datetime(2025, 6, 5, 16, 45)),  # Анна, одобрена
            # ===== ПРОГРАММИСТСКИЙ МАРАФОН (ID=2) =====
            (2, 5, 1, datetime(2025, 6, 6, 9, 15)),  # Алексей, на рассмотрении
            (2, 7, 2, datetime(2025, 6, 7, 11, 45)),  # Дмитрий, одобрена
            (2, 3, 1, datetime(2025, 6, 8, 13, 20)),  # Иван, на рассмотрении
            (2, 4, 2, datetime(2025, 6, 9, 8, 30)),  # Мария, одобрена
            (2, 6, 3, datetime(2025, 6, 9, 19, 10)),  # Елена, отклонена
            # ===== ВЕСЕННЕ-ЛЕТНЯЯ ФИЗИЧЕСКАЯ ОЛИМПИАДА (ID=3) =====
            (3, 6, 3, datetime(2025, 5, 26, 16, 20)),  # Елена, отклонена
            (3, 3, 1, datetime(2025, 6, 1, 8, 30)),  # Иван, на рассмотрении
            (3, 7, 2, datetime(2025, 6, 2, 12, 15)),  # Дмитрий, одобрена
            (3, 5, 1, datetime(2025, 6, 3, 17, 45)),  # Алексей, на рассмотрении
            (3, 8, 2, datetime(2025, 6, 4, 10, 30)),  # Анна, одобрена
            # ===== ХИМИЧЕСКИЙ ТУРНИР (ID=4) =====
            (4, 4, 1, datetime(2025, 6, 9, 12, 0)),  # Мария, на рассмотрении
            (4, 7, 2, datetime(2025, 6, 9, 14, 30)),  # Дмитрий, одобрена
            (4, 5, 1, datetime(2025, 6, 10, 8, 15)),  # Алексей, на рассмотрении
            (4, 8, 3, datetime(2025, 6, 10, 11, 45)),  # Анна, отклонена
            # ===== IT-ХАКАТОН (ID=5) =====
            (5, 5, 1, datetime(2025, 6, 10, 7, 0)),  # Алексей, на рассмотрении
            (5, 3, 1, datetime(2025, 6, 10, 9, 30)),  # Иван, на рассмотрении
            (5, 7, 2, datetime(2025, 6, 10, 11, 15)),  # Дмитрий, одобрена
            (5, 4, 1, datetime(2025, 6, 10, 13, 45)),  # Мария, на рассмотрении
            # ===== БУДУЩИЕ ОЛИМПИАДЫ (для тестирования списков) =====
            # Математическая олимпиада МГУ (ID=6)
            (6, 3, 1, datetime(2025, 6, 5, 15, 0)),  # Иван, на рассмотрении
            (6, 4, 1, datetime(2025, 6, 6, 16, 30)),  # Мария, на рассмотрении
            (6, 5, 2, datetime(2025, 6, 7, 10, 15)),  # Алексей, одобрена
            # Физическая олимпиада МФТИ (ID=7)
            (7, 7, 1, datetime(2025, 6, 8, 14, 20)),  # Дмитрий, на рассмотрении
            (7, 6, 3, datetime(2025, 6, 9, 12, 45)),  # Елена, отклонена
            # Химическая олимпиада СПбГУ (ID=8)
            (8, 8, 1, datetime(2025, 6, 10, 9, 0)),  # Анна, на рассмотрении
        ]
        await conn.executemany(
            "INSERT INTO Application (olympiad_id, user_id, status_id, created_date) VALUES ($1, $2, $3, $4)",
            applications_data,
        )

        print("💬 Добавляем сообщения модераторов...")

        # Сообщения модераторов к заявкам
        messages_data = [
            # === ОДОБРЕННЫЕ ЗАЯВКИ ===
            # Летняя математика - Иван (application_id=1)
            (
                2,
                1,
                "Заявка одобрена! Не забудьте подготовить справочные материалы для олимпиады. Список литературы отправлен на почту.",
                datetime(2025, 6, 2, 15, 0),
            ),
            # Летняя математика - Анна (application_id=4)
            (
                1,
                4,
                "Поздравляем! Ваша заявка принята. Ожидайте дополнительную информацию о формате проведения.",
                datetime(2025, 6, 5, 18, 0),
            ),
            # Программистский марафон - Дмитрий (application_id=6)
            (
                1,
                6,
                "Отличная заявка! Ждём вас на марафоне. Проверьте настройки IDE и установите необходимые инструменты.",
                datetime(2025, 6, 7, 12, 0),
            ),
            # Программистский марафон - Мария (application_id=8)
            (
                2,
                8,
                "Заявка одобрена! Рекомендуем повторить алгоритмы сортировки и структуры данных.",
                datetime(2025, 6, 9, 10, 30),
            ),
            # Физическая олимпиада - Дмитрий (application_id=12)
            (
                1,
                12,
                "Ваша заявка принята! Не забудьте взять калькулятор и справочник по физическим константам.",
                datetime(2025, 6, 2, 14, 20),
            ),
            # Физическая олимпиада - Анна (application_id=14)
            (
                2,
                14,
                "Заявка одобрена. Удачи на олимпиаде! Ознакомьтесь с регламентом проведения.",
                datetime(2025, 6, 4, 11, 45),
            ),
            # Химический турнир - Дмитрий (application_id=16)
            (
                1,
                16,
                "Принято! Будет интересно. Повторите органическую химию и реакции комплексообразования.",
                datetime(2025, 6, 9, 15, 15),
            ),
            # IT-хакатон - Дмитрий (application_id=21)
            (
                2,
                21,
                "Заявка одобрена! Хакатон будет проходить 48 часов. Подготовьте команду и идеи.",
                datetime(2025, 6, 10, 12, 30),
            ),
            # Будущие олимпиады
            (1, 25, "Заявка на МГУ одобрена! Следите за обновлениями на сайте.", datetime(2025, 6, 7, 11, 0)),
            # === ОТКЛОНЕННЫЕ ЗАЯВКИ ===
            # Летняя математика - Елена (application_id=3)
            (
                2,
                3,
                "К сожалению, заявка отклонена. Недостаточно опыта в высшей математике. Рекомендуем участие в подготовительных курсах.",
                datetime(2025, 6, 4, 10, 30),
            ),
            # Программистский марафон - Елена (application_id=9)
            (
                1,
                9,
                "Заявка отклонена. Требуется больше опыта в алгоритмическом программировании. Попробуйте сначала участвовать в школьных турнирах.",
                datetime(2025, 6, 9, 20, 15),
            ),
            # Физическая олимпиада - Елена (application_id=11)
            (
                2,
                11,
                "К сожалению, не хватает базовых знаний по физике. Рекомендуем подготовиться и попробовать в следующий раз.",
                datetime(2025, 5, 26, 17, 0),
            ),
            # Химический турнир - Анна (application_id=18)
            (
                1,
                18,
                "Заявка отклонена. Требуются более глубокие знания неорганической химии.",
                datetime(2025, 6, 10, 13, 0),
            ),
            # Будущие олимпиады
            (2, 26, "Заявка на МФТИ отклонена. Не соответствует возрастным требованиям.", datetime(2025, 6, 9, 14, 30)),
            # === ДОПОЛНИТЕЛЬНЫЕ КОММЕНТАРИИ ===
            # Несколько заявок с комментариями на рассмотрении
            (1, 2, "Заявка принята к рассмотрению. Проверяем документы об образовании.", datetime(2025, 6, 3, 16, 0)),
            (
                2,
                5,
                "Рассматриваем вашу заявку. Результат будет известен в течение 2 дней.",
                datetime(2025, 6, 6, 11, 30),
            ),
            (1, 7, "Заявка на рассмотрении. Ожидаем подтверждения от организаторов.", datetime(2025, 6, 8, 14, 45)),
            (2, 15, "Документы проверяются. Решение будет принято завтра.", datetime(2025, 6, 9, 13, 20)),
            (1, 19, "Заявка поступила в обработку. Ожидайте результат.", datetime(2025, 6, 10, 8, 45)),
        ]
        await conn.executemany(
            "INSERT INTO Messages (user_id, application_id, message_text, sent_date) VALUES ($1, $2, $3, $4)",
            messages_data,
        )

        print("🎉 База данных успешно инициализирована!")

        # Проверочная статистика
        user_count = await conn.fetchval("SELECT COUNT(*) FROM Users")
        olympiad_count = await conn.fetchval("SELECT COUNT(*) FROM Olympiad")
        application_count = await conn.fetchval("SELECT COUNT(*) FROM Application")
        active_olympiad_count = await conn.fetchval(
            "SELECT COUNT(*) FROM Olympiad WHERE '2025-06-10'::date BETWEEN start_date AND end_date"
        )

        print(
            f"""
📊 Статистика БД:
   👥 Пользователей: {user_count}
   🏆 Олимпиад: {olympiad_count}
   📋 Заявок: {application_count}
   ✅ Активных на 10.06.2025: {active_olympiad_count}
        """
        )

    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        raise
    finally:
        await conn.close()
        print("🔌 Соединение с БД закрыто")


if __name__ == "__main__":
    asyncio.run(create_tables_and_seed())
