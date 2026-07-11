"""Handlers for user authentication and onboarding.

This module manages user registration flows, integrating Telegram callbacks
with Supabase storage and local in-memory caching.
"""

import logging
from typing import Any

from aiogram import Router, F
from aiogram.types import CallbackQuery
from cachetools import TTLCache
from supabase import AsyncClient

from src.db.crud import register_user_db
from src.keyboards.keyboards import create_profile_kb

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "register_user")
async def register_user(
    callback: CallbackQuery, db: AsyncClient, users_cache: TTLCache[int, Any]
) -> None:
    """Handle the user registration callback process.

    Registers a new user in the Supabase database using their Telegram credentials,
    updates the local TTL cache with the newly created profile, and updates the UI.
    """
    tg_user_id = callback.from_user.id
    tg_username = callback.from_user.username

    try:
        # 1. Намагаємося записати нового користувача в базу даних
        user_data = await register_user_db(
            user_id=tg_user_id, username=tg_username, db=db
        )
        # 2. Оновлюємо кеш: затираємо старий None актуальними даними з БД
        users_cache[tg_user_id] = user_data
    except Exception as e:
        logger.error(f"Помилка бази даних при реєстрації: {e}", exc_info=True)
        await callback.answer(
            "Упс, сталася помилка при реєстрації користувача в дб.", show_alert=True
        )
        return
    await callback.message.edit_text(
        "Успішно зареєстровано", reply_markup=create_profile_kb
    )
