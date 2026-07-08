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


@router.message(Command("help"))
async def help_handler(
    message: Message,
    user_data: UserCacheItem | None
) -> None:
    """Handle the /help command.

    Provide instructions on how to use the bot, dynamic tips based on
    whether the user is registered, and clarify the 24-hour update cycle.
    """
    logger.debug(f"Користувач {message.from_user.id} викликав /help")

    # Базова довідка, яка потрібна всім
    help_text = (
        "🤖 <b>Довідка по роботі з ботом</b>\n\n"
        "Цей бот допомагає автоматично шукати вакансії за твоїми кастомними фільтрами та аналізувати їх за допомогою ШІ.\n\n"
        "⚙️ <b>Як це працює:</b>\n"
        "1. Раз на добу бот збирає нові вакансії з ринку.\n"
        "2. Проганяє їх через твої налаштування (ключові слова та AI-промпт).\n"
        "3. Відправляє сповіщення про нові знайдені вакансії.\n"
        "4. Додає їх до твого особистого списку збережених вакансій.\n\n"
    )

    # Додаємо динамічні підказки залежно від статусу користувача
    if not user_data:
        help_text += (
            "📌 <b>Твій статус:</b> Не зареєстрований.\n"
            "Щоб почати, натисни кнопку нижче або відправ команду /start"
        )
        await message.reply(text=help_text, reply_markup=not_registered_kb, parse_mode="HTML")
    else:
        help_text += (
            "📌 <b>Твій статус:</b> Авторизований користувач.\n\n"
            "📋 <b>Основні дії (доступні в меню):</b>\n"
            "• <code>🔍 Мої вакансії</code> — переглянути всі знайдені актуальні вакансії за твоїми пошуковими профілями.\n"
            "• <code>🔧 Додати / змінити профіль</code> — додати пошуковий профіль, можливість створити декілька (наприклад, окремо на Python і на Django).\n"
            "• <code>📋 Мої профілі</code> — перевірити поточні профілі пошуку, видалити не актуальні.\n"
            "• <code>❌ Видалити підписку</code> — якщо ти вже знайшов роботу (вітаємо! 🎉) або сервіс тобі більше не потрібен. Це повністю видалить твій акаунт та всі налаштування з бази даних.\n\n"
            "⏳ <i>Нагадування: якщо ти щойно змінив профіль, зачекай наступного скрапінгу для оновлення результатів.</i>"
        )
        await message.reply(text=help_text, reply_markup=registered_kb, parse_mode="HTML")