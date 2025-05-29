from aiogram import Dispatcher
from handlers import base_router

def get_dispatcher():
    """Создание и настройка диспетчера"""
    dp = Dispatcher()
    
    # Позже здесь будут подключены роутеры
    dp.include_router(base_router)
    
    return dp
