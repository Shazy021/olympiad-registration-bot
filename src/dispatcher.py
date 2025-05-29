from aiogram import Dispatcher

def get_dispatcher():
    """Создание и настройка диспетчера"""
    dp = Dispatcher()
    
    # Позже здесь будут подключены роутеры
    # dp.include_router(some_router)
    
    return dp
