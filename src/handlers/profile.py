"""Handlers for user search profiles and FSM onboarding wizard.

This module implements the Finite State Machine (FSM) for creating,
previewing, saving, listing, and deleting search filters (profiles),
as well as managing account unsubscription routines.
"""

import html
import logging
from typing import Any

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from supabase import AsyncClient

from src.exceptions import EmptyResponse
from src.db.crud import (
    create_or_update_profile_db,
    get_user_profiles_from_db,
    delete_profile_from_db,
    delete_user_from_db
)
from src.keyboards.keyboards import (
    registered_kb,
    save_or_remake_profile_kb,
    create_profile_kb,
    to_main_button,
    delete_subscription_button
)
from src.middlewares.user import UserCacheItem

logger = logging.getLogger(__name__)

router = Router()


class Profile(StatesGroup):
    """FSM states group for the search profile creation wizard."""
    name: str = State()
    exclude_keywords: list = State()
    include_keywords: list = State()
    query_text: str = State()


@router.callback_query(F.data == "create_profile")
async def create_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """Start the FSM wizard for creating a new search profile."""
    await state.clear()
    logger.debug("Користувач %s розпочав створення профілю", callback.from_user.id)

    await state.set_state(Profile.name)
    await callback.message.answer(
        "📝 **Введіть ім'я для нового профілю пошуку**\n\n"
        "💡 Ви можете створити кілька різних профілів (наприклад: *Python Junior*, *Data Analyst*).\n\n"
        "⚠️ **Важливо:** якщо ввести назву профілю, який уже існує, новий профіль перезапише старий!"
    )
    await callback.answer()

@router.message(Profile.name)
async def add_name_ask_for_include_filters(message: Message, state: FSMContext) -> None:
    """Save profile name and request inclusion keywords."""
    logger.debug("FSM: Збереження імені профілю для %s", message.from_user.id)
    await state.update_data(name=message.text)

    await state.set_state(Profile.include_keywords)
    await message.answer(
        "🔍 **Які ключові слова шукати в назві вакансії?**\n\n"
        "Введіть слова через пробіл. Бот шукатиме вакансії, які містять **хоча б одне** з них.\n"
        "_(Наприклад: python django backend)_\n\n"
        "🚫 Якщо цей фільтр не потрібен, просто введіть **pass**",
        parse_mode="Markdown"
    )

@router.message(Profile.include_keywords)
async def add_include_ask_for_exclude_filters(message: Message, state: FSMContext) -> None:
    """Save inclusion keywords and request exclusion (stop) keywords."""
    logger.debug("FSM: Збереження include_keywords для %s", message.from_user.id)
    text = message.text or "pass"
    key_words = text.lower().strip().split()

    await state.update_data(include_keywords=[] if key_words == ["pass"] else key_words)
    await state.set_state(Profile.exclude_keywords)
    await message.answer(
        "❌ **Введіть стоп-слова (слова-винятки)**\n\n"
        "Введіть через пробіл слова, яких **НЕ повинно бути** в назві вакансії. "
        "Якщо бот знайде бодай одне з них, він пропустить цю вакансію.\n"
        "_(Наприклад: senior crypto manager sales)_\n\n"
        "🚫 Якщо цей фільтр не потрібен, просто введіть **pass**",
        parse_mode="Markdown"
    )

@router.message(Profile.exclude_keywords)
async def add_exclude_ask_for_prompt(message: Message, state: FSMContext) -> None:
    """Save exclusion keywords and request AI filter prompt."""
    logger.debug("FSM: Збереження exclude_keywords для %s", message.from_user.id)
    text = message.text or "pass"
    key_words = text.lower().strip().split()
    await state.update_data(exclude_keywords=[] if key_words == ["pass"] else key_words)
    await state.set_state(Profile.query_text)

    await message.answer(
        "🤖 **Налаштування AI-фільтра (аналіз вакансії за допомогою ШІ)**\n\n"
        "Опишіть своїми словами, що саме нейромережа має шукати або перевіряти в повному описі вакансії.\n"
        "_(Наприклад: «Відсіюй вакансії, де вимагають знання англійської вище B1» або «Шукай тільки позиції з можливістю повного ремонтауту»)_\n\n"
        "⏩ Якщо цей фільтр не потрібен, просто введіть **pass**",
        parse_mode="Markdown"
    )

@router.message(Profile.query_text)
async def add_prompt_create_profile_in_db(
        message: Message, state: FSMContext, user_data: dict
) -> None:
    """Process AI prompt, validate input data, and render configuration preview."""
    logger.debug("FSM: Фіналізація профілю для %s", message.from_user.id)
    text = message.text.strip()
    await state.update_data(query_text="" if text.lower() == "pass" else text)

    raw_data = await state.get_data()

    has_filters = (
            bool(raw_data.get("include_keywords")) or
            bool(raw_data.get("exclude_keywords")) or
            bool(raw_data.get("query_text"))
    )


    if not has_filters:
        username = user_data.get("username") or message.from_user.first_name

        # 1. Повідомляємо про помилку
        await message.answer(
            "⚠️ **Помилка створення профілю**\n\n"
            "Ви не ввели жодного фільтра пошуку (скрізь вказали `pass`).\n\n"
            f"🗣 _«Все хуйня, {username}, давай по новой.»_\n\n"
            "🔄 Повертаємось на початок.",
            parse_mode="Markdown"
        )

        # 2. Очищаємо дані в state, але зберігаємо структуру FSM
        await state.set_data({})

        # 3. Переводимо на початковий крок
        await state.set_state(Profile.name)

        # 4. Повторюємо перше запитання з create_profile
        await message.answer(
            "📝 **Введіть ім'я для нового профілю пошуку**\n\n"
            "💡 Ви можете створити кілька різних профілів (наприклад: *Python Junior*, *Data Analyst*).\n\n"
            "⚠️ **Важливо:** якщо ввести назву профілю, який уже існує, новий профіль перезапише старий!"
        )
        return

    inc_words = ", ".join(raw_data.get("include_keywords", [])) or "не вказано"
    exc_words = ", ".join(raw_data.get("exclude_keywords", [])) or "не вказано"
    ai_prompt = raw_data.get("query_text") or "не вказано"

    preview_text = (
        f"📊 <b>Попередній перегляд профілю:</b>\n\n"
        f"🔹 <b>Ім'я профілю:</b> {html.escape(raw_data['name'])}\n"
        f"➕ Шукати слова: <code>{html.escape(inc_words)}</code>\n"
        f"➖ Ігнорувати слова: <code>{html.escape(exc_words)}</code>\n"
        f"🤖 AI-промпт: <i>{html.escape(ai_prompt)}</i>"
    )
    await message.reply(
        text=preview_text,
        reply_markup=save_or_remake_profile_kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "save_profile")
async def save_profile(
        callback: CallbackQuery, state: FSMContext, user_data: dict, db: AsyncClient
) -> None:
    """Save the constructed FSM profile into the Supabase database."""
    profile_data = await state.get_data()
    await state.clear()
    profile_data["user_id"] = user_data.get("id")

    try:
        await create_or_update_profile_db(profile_data=profile_data, db=db)
        await callback.message.answer("Профіль фільтрації збережено")
        await callback.message.answer(text=f"Головне меню", reply_markup=registered_kb)
    except Exception as e:
        logger.error("Помилка збереження профілю в БД: %s", e, exc_info=True)
        await callback.message.answer("Сталася помилка бази даних при збереженні профілю.")
    await callback.answer()

@router.callback_query(F.data == "show_profiles")
async def show_profiles(callback: CallbackQuery, user_data: UserCacheItem, db: AsyncClient) -> None:
    """Fetch and display all search profiles associated with the user."""
    try:
        profiles_list: list[dict[str, Any]] = await get_user_profiles_from_db(
            user_db_id=user_data.get("id"), db=db
        )

        for index, profile in enumerate(profiles_list):
            buttons = [
                [InlineKeyboardButton(text="❌ Видалити профіль фільтрації", callback_data=f"delete_profile:{profile['id']}")]
            ]

            # Якщо це ОСТАННІЙ профіль у списку, додаємо кнопку меню другим рядком
            if index == len(profiles_list) - 1:
                buttons.append(
                    [to_main_button]
                )

            delete_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

            await callback.message.answer(
                text=f"📋 **Ім'я профілю:** {profile['name']}\n"
                     f"➕ Включити слова: {', '.join(profile['include_keywords']) if profile['include_keywords'] else 'немає'}\n"
                     f"➖ Виключити слова: {', '.join(profile['exclude_keywords']) if profile['exclude_keywords'] else 'немає'}\n"
                     f"🤖 Промпт: {profile['query_text'] or 'немає'}",
                reply_markup=delete_kb,
                parse_mode="Markdown"
            )
        await callback.answer()

    except EmptyResponse:
        await callback.message.answer(
            text="У вас поки нема жодного профілю",reply_markup=create_profile_kb
        )
        await callback.answer()
    except Exception as e:
        logger.error("Помилка при отриманні профілів з БД: %s", e, exc_info=True)
        await callback.message.answer("Помилка завантаження даних з бази даних.")
        await callback.answer()



@router.callback_query(F.data.startswith("delete_profile:"))
async def handle_delete_profile(callback: CallbackQuery, db: AsyncClient):
    """Delete a specific search profile from the database by its ID."""
    # Дістаємо ID профілю з callback_data (розбиваємо рядок по двокрапці)
    profile_id = int(callback.data.split(":")[1])

    try:
        await delete_profile_from_db(profile_id=profile_id, db=db)
        await callback.answer("Профіль успішно видалено!", show_alert=False)
        await callback.message.edit_text("🗑 Цей профіль було видалено.")

    except Exception as e:
        logger.error("Помилка видалення профілю %s: %s", profile_id, e, exc_info=True)
        await callback.answer("Не вдалося видалити профіль через помилку БД.", show_alert=True)

@router.callback_query(F.data == "to_main")
async def to_main(callback: CallbackQuery) -> None:
    """Redirect user UI back to the main menu."""
    await callback.message.edit_text(text="Головне меню", reply_markup=registered_kb)
    await callback.answer()

@router.callback_query(F.data == "unsubscribe")
async def unsubscribe(callback: CallbackQuery):
    """Prompt user for confirmation before deleting subscription and account data."""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [delete_subscription_button],
            [to_main_button]
        ]
    )
    await callback.message.edit_text(
        text="Ви впевнені, що хочете скасувати підписку?",
        reply_markup=kb
    )
    await callback.answer(
        text="⚠️ УВАГА! Натиснувши 'Видалити', будуть видалені всі ваші профілі пошуку та знайдені вакансії!",
        show_alert=True
    )


@router.callback_query(F.data == "delete_subscription")
async def delete_subscription(
        callback: CallbackQuery, users_cache: dict, user_data: dict, db: AsyncClient
) -> None:
    """Permanently delete user record from database and clear local RAM cache."""
    user_db_id = user_data.get("id")
    tg_user_id = callback.from_user.id
    # Видаляємо з ін-меморі кешу
    users_cache.pop(tg_user_id, None)

    #remove from db
    try:
        await delete_user_from_db(user_id=user_db_id, db=db)
        await callback.message.edit_text("Ваш профіль та підписку успішно видалено.")
        logger.info("Користувач TG:%s (DB:%s) видалив підписку.", tg_user_id, user_db_id)
    except Exception as e:
        logger.error("Помилка при видаленні користувача %s з БД: %s", user_db_id, e, exc_info=True)
        await callback.message.edit_text("Сталася помилка при видаленні з бази даних.")
    await callback.answer()

