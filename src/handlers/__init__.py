from .menu import router as menu_router
from .registration import router as registration_router
from .delete_account import router as account_del_router
from .application_moderation import router as application_moderation_router
from .application import router as application_router
from .olympiad_management import router as olympiad_management_router

__all__ = [
    'registration_router',
    'menu_router',
    'account_del_router',
    'application_moderation_router',
    'application_router',
    'olympiad_management_router'
]