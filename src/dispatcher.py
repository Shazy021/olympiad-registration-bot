from aiogram import Dispatcher
from handlers import registration_router, menu_router

def get_dispatcher():
    """Создание и настройка диспетчера"""
    dp = Dispatcher()
    
    # Позже здесь будут подключены роутеры
    dp.include_router(registration_router)
    dp.include_router(menu_router)
    
    return dp
