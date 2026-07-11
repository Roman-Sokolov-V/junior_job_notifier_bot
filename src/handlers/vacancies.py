"""Handlers for managing and displaying saved user vacancies.

This module fetches bookmarked job listings from Supabase and renders them
to the user, ensuring compliance with Telegram message length constraints.
"""

import logging
from typing import Any

from aiogram import Router, F
from aiogram.types import CallbackQuery

from supabase import AsyncClient

from src.db.crud import get_user_vacancies_from_db
from src.keyboards.keyboards import registered_kb

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data == "vacancy")
async def my_vac(callback: CallbackQuery, db: AsyncClient, user_data:dict):
    """Fetch and display all vacancies bookmarked by the user.

    Aggregates job URLs and sends them back to the user, splitting the payload
    into chunks if the total text length exceeds Telegram's 4096-character limit.
    """
    try:
        vacancies: list[dict[str, Any]] = await get_user_vacancies_from_db(
            user_db_id=user_data["id"], db=db
        )
        if not vacancies:
            await callback.message.answer(
                text="📋 **У вас поки немає збережених вакансій.**\n\n"
                     "💡 **Як це працює:** Бот збирає нові вакансії та аналізує їх під ваші фільтри **один раз на добу**.\n\n"
                     "⏳ Якщо ви щойно налаштували пошук, будь ласка, зачекайте — перша підбірка з'явиться протягом 24 годин.",
                reply_markup=registered_kb,
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        #  Захист від ліміту Telegram (4096 символів)
        # Збираємо посилання порціями, щоб повідомлення не падало
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0
        for vac in vacancies:
            vac_text = f"{vac['title']}/n{vac['url']}"
            vac_length = len(vac_text)
            if current_length + vac_length  > 4090:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [vac_text]
                current_length = 1
            else:
                current_chunk.append(vac_text)
                current_length += len(vacancies) + 4
        # останній посилаємо з клавіатурою
        await callback.message.answer(
            text="\n\n".join(current_chunk),
            reply_markup=registered_kb
        )

    except Exception as e:
        logger.error(
            "Помилка бази даних при отриманні вакансій для користувача %s: %s",
            user_data.get("id"), e, exc_info=True
        )
        await callback.message.answer("Упс, сталася помилка при отриманні вакансій з бази даних.")
        await callback.answer()
