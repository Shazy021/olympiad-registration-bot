from aiogram import Dispatcher
from handlers import (
    registration_router,
    menu_router,
    account_del_router,
    application_moderation_router,
    application_router,
    olympiad_management_router
)

def get_dispatcher():
    """Создание и настройка диспетчера"""
    dp = Dispatcher()
    
    # Позже здесь будут подключены роутеры
    dp.include_router(registration_router)
    dp.include_router(menu_router)
    dp.include_router(account_del_router)
    dp.include_router(application_moderation_router)
    dp.include_router(application_router)
    dp.include_router(olympiad_management_router)
    
    return dp
