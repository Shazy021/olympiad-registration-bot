from .menu import router as menu_router
from .registration import router as registration_router
from .delete_account import router as account_del_router

__all__ = ['registration_router', 'menu_router', 'account_del_router']