from aiogram import Router

from .start import router as start_router
from .not_registered_user import router as not_registered_user_router
from .profile import router as filters_router
from .vacancies import router as vacancies_router
from .me import router as me_router

router = Router(name="main_handlers_router")

router.include_routers(
    start_router,
    not_registered_user_router,
    filters_router,
    vacancies_router,
    me_router,
)

__all__ = ["router"]
