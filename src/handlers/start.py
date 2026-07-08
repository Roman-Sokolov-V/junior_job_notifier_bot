"""Handlers for core system commands.

This module processes high-level user commands such as /start,
routing users based on their registration status provided by the cache middleware.
"""
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.keyboards.keyboards import not_registered_kb, registered_kb
from src.middlewares.user import UserCacheItem

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command('start'))
async def start(message: Message, user_data: UserCacheItem | None):
    """Handle the /start command.

    Greet the user if they are already registered in the system,
    otherwise prompt them to start the onboarding/registration process.
    """
    if not user_data:
        logger.debug(f"Незареєстрований користувач {message.from_user.id} викликав /start")
        await message.reply(
            text="Ви не зареєстровані. Бажаєте зареєструватися?",
            reply_markup=not_registered_kb
        )
    else:
        logger.debug(f"Зареєстрований користувач {message.from_user.id} зайшов у бот")
        await message.reply(
            text=f"Привіт {user_data['username']}",
            reply_markup=registered_kb
        )
