"""Handlers for user search profiles and FSM onboarding wizard.

This module implements the Finite State Machine (FSM) for creating,
previewing, saving, listing, and deleting search filters (profiles),
as well as managing account unsubscription routines.
"""

import html
import logging
from typing import Any

import mimetypes
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from supabase import AsyncClient

from src.exceptions import EmptyResponse
from src.db.crud import (
    create_or_update_profile_db,
    get_user_profiles_from_db,
    delete_profile_from_db,
    delete_user_from_db,
)
from src.keyboards.keyboards import (
    registered_kb,
    save_or_remake_profile_kb,
    create_profile_kb,
    to_main_button,
    delete_subscription_button,
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
    file: str = State()


#
# @router.callback_query(F.data == "create_profile")
# async def create_profile(callback: CallbackQuery, state: FSMContext) -> None:
#     """Start the FSM wizard for creating a new search profile."""
#     await state.clear()
#     logger.debug("Користувач %s розпочав створення профілю", callback.from_user.id)
#
#     await state.set_state(Profile.name)
#     await callback.message.edit_text(
#         "📝 **Введіть ім'я для нового профілю пошуку**\n\n"
#         "💡 Ви можете створити кілька різних профілів (наприклад: *Python Junior*, *Data Analyst*).\n\n"
#         "⚠️ **Важливо:** якщо ввести назву профілю, який уже існує, новий профіль перезапише старий!"
#     )
#     await callback.answer()
#
#
# @router.message(Profile.name)
# async def add_name_ask_for_include_filters(message: Message, state: FSMContext) -> None:
#     """Save profile name and request inclusion keywords."""
#     logger.debug("FSM: Збереження імені профілю для %s", message.from_user.id)
#     await state.update_data(name=message.text)
#
#     await state.set_state(Profile.include_keywords)
#     await message.answer(
#         "🔍 **Які ключові слова шукати в назві вакансії?**\n\n"
#         "Введіть слова через пробіл. Бот шукатиме вакансії, які містять **хоча б одне** з них.\n"
#         "_(Наприклад: python django backend)_\n\n"
#         "🚫 Якщо цей фільтр не потрібен, просто введіть **pass**",
#         parse_mode="Markdown",
#     )
#
#
# @router.message(Profile.include_keywords)
# async def add_include_ask_for_exclude_filters(
#     message: Message, state: FSMContext
# ) -> None:
#     """Save inclusion keywords and request exclusion (stop) keywords."""
#     logger.debug("FSM: Збереження include_keywords для %s", message.from_user.id)
#     text = message.text or "pass"
#     key_words = text.lower().strip().split()
#
#     await state.update_data(include_keywords=[] if key_words == ["pass"] else key_words)
#     await state.set_state(Profile.exclude_keywords)
#     await message.answer(
#         "❌ **Введіть стоп-слова (слова-винятки)**\n\n"
#         "Введіть через пробіл слова, яких **НЕ повинно бути** в назві вакансії. "
#         "Якщо бот знайде бодай одне з них, він пропустить цю вакансію.\n"
#         "_(Наприклад: senior crypto manager sales)_\n\n"
#         "🚫 Якщо цей фільтр не потрібен, просто введіть **pass**",
#         parse_mode="Markdown",
#     )
#
#
# @router.message(Profile.exclude_keywords)
# async def add_exclude_ask_for_prompt(message: Message, state: FSMContext) -> None:
#     """Save exclusion keywords and request AI filter prompt."""
#     logger.debug("FSM: Збереження exclude_keywords для %s", message.from_user.id)
#     text = (message.text or "pass").strip()
#     key_words = text.lower().split()
#     await state.update_data(exclude_keywords=[] if key_words == ["pass"] else key_words)
#     await state.set_state(Profile.query_text)
#
#     await message.answer(
#         "🤖 **Налаштування AI-фільтра (аналіз вакансії за допомогою ШІ)**\n\n"
#         "Опишіть своїми словами, що саме нейромережа має перевіряти в описі вакансії.\n"
#         "_(Наприклад: «Відсіюй вакансії, де вимагають знання англійської вище B1»)_\n\n"
#         "💡 **Зверніть увагу:** завантаження резюме (CV) буде доступне **тільки за наявності AI-промпту**, "
#         "оскільки ШІ аналізує документ саме на основі ваших вказівок.\n\n"
#         "⏩ Якщо AI-аналіз та резюме не потрібні, просто введіть **pass**",
#         parse_mode="Markdown",
#     )
#
# MAX_FILE_SIZE_MB = 2
# MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
#
# @router.message(Profile.query_text)
# async def add_prompt_ask_for_cv(
#     message: Message, state: FSMContext, user_data: dict
# ) -> None:
#     """Save AI prompt and conditionally ask for CV document or skip to preview."""
#     logger.debug("FSM: Збереження query_text для %s", message.from_user.id)
#     text = (message.text or "").strip()
#     is_pass = text.lower() == "pass"
#
#     query_text = "" if is_pass else text
#     await state.update_data(query_text=query_text)
#
#     # 🛑 ЛОГІКА ОПТИМІЗАЦІЇ: Якщо AI-промпт відсутній — CV використовувати неможливо
#     if not query_text:
#         # Гарантовано скидаємо дані CV в None
#         await state.update_data(cv_bytes=None, cv_filename=None, cv_mime=None)
#
#         await message.answer(
#             "ℹ️ **Завантаження CV пропущено**\n\n"
#             "Оскільки AI-фільтр не налаштовано (ви вказали `pass`), завантаження резюме недоступне, "
#             "адже аналіз CV працює виключно в зв'язці з AI-запитом.\n"
#             "Формуємо попередній перегляд...",
#             parse_mode="Markdown",
#         )
#         # Одразу переходимо до перегляду профілю
#         await _render_and_send_preview(message, state, user_data)
#         return
#
#     # Якщо промпт є — пропонуємо завантажити CV
#     await state.set_state(Profile.file)
#
#     await message.answer(
#         f"📄 **Завантаження вашого CV (резюме не більше {MAX_FILE_SIZE_MB} мб)**\n\n"
#         f"Надішліть файл вашого резюме (підтримуються **PDF** або **TXT**).\n"
#         f"ШІ порівнюватиме ваші навички з вимогами вакансії на основі вашого AI-запиту і CV.\n\n"
#         f"⏩ Якщо ви не хочете додавати резюме, просто введіть **pass**",
#         parse_mode="Markdown",
#     )
#
#
#
# @router.message(Profile.file)
# async def process_cv_and_show_preview(
#     message: Message, state: FSMContext, user_data: dict, bot
# ) -> None:
#     """Process CV file input with size and format validation, then render preview."""
#     logger.debug("FSM: Перевірка CV та збір прев'ю для %s", message.from_user.id)
#
#     raw_data = await state.get_data()
#
#     # Запобіжник: якщо з якоїсь причини немає query_text, файл не приймаємо
#     if not raw_data.get("query_text"):
#         await state.update_data(cv_bytes=None, cv_filename=None, cv_mime=None)
#         await _render_and_send_preview(message, state, user_data)
#         return
#
#     # 1. Обробка файлу (якщо надіслано документ)
#     if message.document:
#         doc = message.document
#
#         # 🛑 ПЕРЕВІРКА 1: Розмір файлу з метаданих Telegram
#         if doc.file_size and doc.file_size > MAX_FILE_SIZE:
#             file_size_mb = round(doc.file_size / (1024 * 1024), 2)
#             await message.answer(
#                 f"❌ **Файл занадто великий!**\n\n"
#                 f"Розмір вашого файлу: **{file_size_mb} МБ**.\n"
#                 f"Максимально дозволений розмір: **{MAX_FILE_SIZE_MB} МБ**.\n\n"
#                 f"Будь ласка, стисніть файл або надішліть інший (або введіть **pass**)."
#             )
#             return
#
#         # 🛑 ПЕРЕВІРКА 2: Формат/MIME-тип файлу
#         mime_type = doc.mime_type or (mimetypes.guess_type(doc.file_name or "")[0])
#         allowed_mimes = ["application/pdf", "text/plain"]
#
#         if mime_type not in allowed_mimes:
#             await message.answer(
#                 "❌ **Непідтримуваний формат файлу!**\n\n"
#                 "Будь ласка, надішліть резюме у форматі **PDF** або **TXT** (або введіть **pass** для пропуску)."
#             )
#             return
#
#         # Завантажуємо байти файлу з Telegram в оперативну пам'ять
#         telegram_file = await bot.get_file(doc.file_id)
#         file_buffer = await bot.download_file(telegram_file.file_path)
#         file_bytes = file_buffer.read()
#
#         # 🛑 ПЕРЕВІРКА 3: Фактичний розмір у пам'яті
#         if len(file_bytes) > MAX_FILE_SIZE:
#             await message.answer(
#                 f"❌ **Файл перевищує ліміт у {MAX_FILE_SIZE_MB} МБ!** Будь ласка, завантажте менший файл."
#             )
#             return
#
#         # Зберігаємо байти та метадані в FSM
#         await state.update_data(
#             cv_bytes=file_bytes,
#             cv_filename=doc.file_name or "cv.pdf",
#             cv_mime=mime_type,
#         )
#
#     elif message.text and message.text.lower().strip() == "pass":
#         # Скидаємо дані про файл в FSM
#         await state.update_data(cv_bytes=None, cv_filename=None, cv_mime=None)
#     else:
#         await message.answer(
#             "⚠️ Будь ласка, надішліть **документ** (PDF/TXT до 2 МБ) або введіть **pass**."
#         )
#         return
#
#     # 2. Формуємо та відправляємо прев'ю
#     await _render_and_send_preview(message, state, user_data)
#
#
#
#
# async def _render_and_send_preview(
#         message: Message, state: FSMContext, user_data: dict
# ) -> None:
#     """Допоміжна функція для перевірки наявності фільтрів та відправки прев'ю."""
#     raw_data = await state.get_data()
#
#     # Перевірка на наявність хоча б одного фільтра
#     has_filters = (
#             bool(raw_data.get("include_keywords"))
#             or bool(raw_data.get("exclude_keywords"))
#             or bool(raw_data.get("query_text"))
#     )
#
#     if not has_filters:
#         username = user_data.get("username") or message.from_user.first_name
#
#         await message.answer(
#             "⚠️ **Помилка створення профілю**\n\n"
#             "Ви не ввели жодного фільтра пошуку (скрізь вказали `pass`).\n\n"
#             f"🗣 _«Все хуйня, {username}, давай по новой.»_\n\n"
#             "🔄 Повертаємось на початок.",
#             parse_mode="Markdown",
#         )
#
#         await state.set_data({})
#         await state.set_state(Profile.name)
#
#         await message.answer(
#             "📝 **Введіть ім'я для нового профілю пошуку**\n\n"
#             "💡 Ви можете створити кілька різних профілів (наприклад: *Python Junior*, *Data Analyst*).\n\n"
#             "⚠️ **Важливо:** якщо ввести назву профілю, який уже існує, новий профіль перезапише старий!"
#         )
#         return
#
#     # Формуємо прев'ю профілю
#     inc_words = ", ".join(raw_data.get("include_keywords", [])) or "не вказано"
#     exc_words = ", ".join(raw_data.get("exclude_keywords", [])) or "не вказано"
#     ai_prompt = raw_data.get("query_text") or "не вказано"
#
#     cv_filename = raw_data.get("cv_filename")
#     cv_status = (
#         f"📄 <code>{html.escape(cv_filename)}</code>"
#         if raw_data.get("cv_bytes") and cv_filename
#         else "не додано ❌"
#     )
#
#     preview_text = (
#         f"📊 <b>Попередній перегляд профілю:</b>\n\n"
#         f"🔹 <b>Ім'я профілю:</b> {html.escape(raw_data.get('name', ''))}\n"
#         f"➕ Шукати слова: <code>{html.escape(inc_words)}</code>\n"
#         f"➖ Ігнорувати слова: <code>{html.escape(exc_words)}</code>\n"
#         f"🤖 AI-промпт: <i>{html.escape(ai_prompt)}</i>\n"
#         f"📎 Резюме (CV): {cv_status}"
#     )
#
#     await message.reply(
#         text=preview_text, reply_markup=save_or_remake_profile_kb, parse_mode="HTML"
#     )
#
#
#
#
# @router.callback_query(F.data == "save_profile")
# async def save_profile(
#     callback: CallbackQuery, state: FSMContext, user_data: dict, db: AsyncClient
# ) -> None:
#     """Save the constructed FSM profile into the Supabase database."""
#     profile_data = await state.get_data()
#
#     if not profile_data:
#         await callback.answer("Дані втрачено ❌", show_alert=True)
#         await callback.message.edit_text(
#             "⚠️ Дані профілю не заповнені або втрачені через неактивність.\n"
#             "Будь ласка, почніть заповнення анкети спочатку."
#         )
#         return
#     profile_data["user_id"] = user_data.get("id")
#
#     try:
#         await create_or_update_profile_db(profile_data=profile_data, db=db)
#         await state.clear()
#         await callback.message.edit_text(
#             text="Профіль фільтрації збережено ✅\n\nГоловне меню",
#             reply_markup=registered_kb
#         )
#     except Exception as e:
#         logger.error("Помилка збереження профілю в БД: %s", e, exc_info=True)
#         await callback.message.answer(
#             "Сталася помилка бази даних при збереженні профілю."
#         )
#
#     await callback.answer()
#
#
# @router.callback_query(F.data == "show_profiles")
# async def show_profiles(
#     callback: CallbackQuery, user_data: UserCacheItem, db: AsyncClient
# ) -> None:
#     """Fetch and display all search profiles associated with the user."""
#     try:
#         profiles_list: list[dict[str, Any]] = await get_user_profiles_from_db(
#             user_db_id=user_data.get("id"), db=db
#         )
#         await callback.message.delete()
#         for index, profile in enumerate(profiles_list):
#             buttons = [
#                 [
#                     InlineKeyboardButton(
#                         text="❌ Видалити профіль фільтрації",
#                         callback_data=f"delete_profile:{profile['id']}",
#                     )
#                 ]
#             ]
#
#             # Якщо це ОСТАННІЙ профіль у списку, додаємо кнопку меню другим рядком
#             if index == len(profiles_list) - 1:
#                 buttons.append([to_main_button])
#
#             delete_kb = InlineKeyboardMarkup(inline_keyboard=buttons)
#
#             await callback.message.answer(
#                 text=f"📋 **Ім'я профілю:** {profile['name']}\n"
#                 f"➕ Включити слова: {', '.join(profile['include_keywords']) if profile['include_keywords'] else 'немає'}\n"
#                 f"➖ Виключити слова: {', '.join(profile['exclude_keywords']) if profile['exclude_keywords'] else 'немає'}\n"
#                 f"🤖 Промпт: {profile['query_text'] or 'немає'}\n"
#                 f" CV файл: {profile['cv_file'].split("/")[-1] if profile['cv_file'] else 'не надано'}",
#                 reply_markup=delete_kb,
#                 parse_mode="Markdown",
#             )
#         await callback.answer()
#
#     except EmptyResponse:
#         await callback.message.answer(
#             text="У вас поки нема жодного профілю", reply_markup=create_profile_kb
#         )
#         await callback.answer()
#     except Exception as e:
#         logger.error("Помилка при отриманні профілів з БД: %s", e, exc_info=True)
#         await callback.message.answer("Помилка завантаження даних з бази даних.")
#         await callback.answer()
#
#
# @router.callback_query(F.data.startswith("delete_profile:"))
# async def handle_delete_profile(callback: CallbackQuery, db: AsyncClient):
#     """Delete a specific search profile from the database by its ID."""
#     # Дістаємо ID профілю з callback_data (розбиваємо рядок по двокрапці)
#     profile_id = int(callback.data.split(":")[1])
#
#     try:
#         await delete_profile_from_db(profile_id=profile_id, db=db)
#         await callback.answer("Профіль успішно видалено!", show_alert=False)
#         await callback.message.edit_text("🗑 Цей профіль було видалено.")
#
#     except Exception as e:
#         logger.error("Помилка видалення профілю %s: %s", profile_id, e, exc_info=True)
#         await callback.answer(
#             "Не вдалося видалити профіль через помилку БД.", show_alert=True
#         )
#
#
# @router.callback_query(F.data == "to_main")
# async def to_main(callback: CallbackQuery) -> None:
#     """Redirect user UI back to the main menu."""
#     await callback.message.edit_text(text="Головне меню", reply_markup=registered_kb)
#     await callback.answer()
#
#
# @router.callback_query(F.data == "unsubscribe")
# async def unsubscribe(callback: CallbackQuery):
#     """Prompt user for confirmation before deleting subscription and account data."""
#     kb = InlineKeyboardMarkup(
#         inline_keyboard=[[delete_subscription_button], [to_main_button]]
#     )
#     await callback.message.edit_text(
#         text="Ви впевнені, що хочете скасувати підписку?", reply_markup=kb
#     )
#     await callback.answer(
#         text="⚠️ УВАГА! Натиснувши 'Видалити', будуть видалені всі ваші профілі пошуку та знайдені вакансії!",
#         show_alert=True,
#     )
#
#
# @router.callback_query(F.data == "delete_subscription")
# async def delete_subscription(
#     callback: CallbackQuery, users_cache: dict, user_data: dict, db: AsyncClient
# ) -> None:
#     """Permanently delete user record from database and clear local RAM cache."""
#     user_db_id = user_data.get("id")
#     tg_user_id = callback.from_user.id
#     # Видаляємо з ін-меморі кешу
#     users_cache.pop(tg_user_id, None)
#
#     # remove from db
#     try:
#         await delete_user_from_db(user_id=user_db_id, db=db)
#         await callback.message.edit_text("Ваш профіль та підписку успішно видалено.")
#         logger.info(
#             "Користувач TG:%s (DB:%s) видалив підписку.", tg_user_id, user_db_id
#         )
#     except Exception as e:
#         logger.error(
#             "Помилка при видаленні користувача %s з БД: %s",
#             user_db_id,
#             e,
#             exc_info=True,
#         )
#         await callback.message.edit_text("Сталася помилка при видаленні з бази даних.")
#     await callback.answer()
#


# ---------------------------------------------------------------------------
# Допоміжні функції формування UI
# ---------------------------------------------------------------------------

def _build_profiles_view(profiles_list: list[dict[str, Any]]) -> tuple[str, InlineKeyboardMarkup]:
    """Формує єдине текстове повідомлення та клавіатуру для списку профілів."""
    text_lines = ["📋 **Ваші профілі пошуку:**\n"]
    keyboard_buttons = []

    for index, profile in enumerate(profiles_list, 1):
        inc = ", ".join(profile['include_keywords']) if profile.get('include_keywords') else "немає"
        exc = ", ".join(profile['exclude_keywords']) if profile.get('exclude_keywords') else "немає"
        prompt = profile.get('query_text') or "немає"

        cv_path = profile.get('cv_file')
        cv_name = cv_path.split("/")[-1] if cv_path else "не надано"

        text_lines.append(
            f"**{index}. {profile['name']}**\n"
            f"➕ Включити: `{inc}`\n"
            f"➖ Виключити: `{exc}`\n"
            f"🤖 Промпт: _{prompt}_\n"
            f"📄 CV: `{cv_name}`\n"
        )

        # Кнопка видалення для кожного профілю
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"❌ Видалити «{profile['name']}»",
                callback_data=f"delete_profile:{profile['id']}"
            )
        ])

    # Кнопка повернення в головне меню внизу
    keyboard_buttons.append([to_main_button])

    return "\n".join(text_lines), InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


# ---------------------------------------------------------------------------
# Хендлери створення профілю (FSM Wizard)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "create_profile")
async def create_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """Start the FSM wizard for creating a new search profile."""
    await state.clear()
    logger.debug("Користувач %s розпочав створення профілю", callback.from_user.id)

    await state.set_state(Profile.name)
    await callback.message.edit_text(
        "📝 **Введіть ім'я для нового профілю пошуку**\n\n"
        "💡 Ви можете створити кілька різних профілів (наприклад: *Python Junior*, *Data Analyst*).\n\n"
        "⚠️ **Важливо:** якщо ввести назву профілю, який уже існує, новий профіль перезапише старий!",
        parse_mode="Markdown"
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
        parse_mode="Markdown",
    )


@router.message(Profile.include_keywords)
async def add_include_ask_for_exclude_filters(
        message: Message, state: FSMContext
) -> None:
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
        parse_mode="Markdown",
    )


@router.message(Profile.exclude_keywords)
async def add_exclude_ask_for_prompt(message: Message, state: FSMContext) -> None:
    """Save exclusion keywords and request AI filter prompt."""
    logger.debug("FSM: Збереження exclude_keywords для %s", message.from_user.id)
    text = (message.text or "pass").strip()
    key_words = text.lower().split()
    await state.update_data(exclude_keywords=[] if key_words == ["pass"] else key_words)
    await state.set_state(Profile.query_text)

    await message.answer(
        "🤖 **Налаштування AI-фільтра (аналіз вакансії за допомогою ШІ)**\n\n"
        "Опишіть своїми словами, що саме нейромережа має перевіряти в описі вакансії.\n"
        "_(Наприклад: «Відсіюй вакансії, де вимагають знання англійської вище B1»)_\n\n"
        "💡 **Зверніть увагу:** завантаження резюме (CV) буде доступне **тільки за наявності AI-промпту**, "
        "оскільки ШІ аналізує документ саме на основі ваших вказівок.\n\n"
        "⏩ Якщо AI-аналіз та резюме не потрібні, просто введіть **pass**",
        parse_mode="Markdown",
    )


MAX_FILE_SIZE_MB = 2
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024


@router.message(Profile.query_text)
async def add_prompt_ask_for_cv(
        message: Message, state: FSMContext, user_data: dict
) -> None:
    """Save AI prompt and conditionally ask for CV document or skip to preview."""
    logger.debug("FSM: Збереження query_text для %s", message.from_user.id)
    text = (message.text or "").strip()
    is_pass = text.lower() == "pass"

    query_text = "" if is_pass else text
    await state.update_data(query_text=query_text)

    if not query_text:
        await state.update_data(cv_bytes=None, cv_filename=None, cv_mime=None)

        await message.answer(
            "ℹ️ **Завантаження CV пропущено**\n\n"
            "Оскільки AI-фільтр не налаштовано (ви вказали `pass`), завантаження резюме недоступне, "
            "адже аналіз CV працює виключно в зв'язці з AI-запитом.\n"
            "Формуємо попередній перегляд...",
            parse_mode="Markdown",
        )
        await _render_and_send_preview(message, state, user_data)
        return

    await state.set_state(Profile.file)

    await message.answer(
        f"📄 **Завантаження вашого CV (резюме не більше {MAX_FILE_SIZE_MB} мб)**\n\n"
        f"Надішліть файл вашого резюме (підтримуються **PDF** або **TXT**).\n"
        f"ШІ порівнюватиме ваші навички з вимогами вакансії на основі вашого AI-запиту і CV.\n\n"
        f"⏩ Якщо ви не хочете додавати резюме, просто введіть **pass**",
        parse_mode="Markdown",
    )


@router.message(Profile.file)
async def process_cv_and_show_preview(
        message: Message, state: FSMContext, user_data: dict, bot
) -> None:
    """Process CV file input with size and format validation, then render preview."""
    logger.debug("FSM: Перевірка CV та збір прев'ю для %s", message.from_user.id)

    raw_data = await state.get_data()

    if not raw_data.get("query_text"):
        await state.update_data(cv_bytes=None, cv_filename=None, cv_mime=None)
        await _render_and_send_preview(message, state, user_data)
        return

    if message.document:
        doc = message.document

        if doc.file_size and doc.file_size > MAX_FILE_SIZE:
            file_size_mb = round(doc.file_size / (1024 * 1024), 2)
            await message.answer(
                f"❌ **Файл занадто великий!**\n\n"
                f"Розмір вашого файлу: **{file_size_mb} МБ**.\n"
                f"Максимально дозволений розмір: **{MAX_FILE_SIZE_MB} МБ**.\n\n"
                f"Будь ласка, стисніть файл або надішліть інший (або введіть **pass**)."
            )
            return

        mime_type = doc.mime_type or (mimetypes.guess_type(doc.file_name or "")[0])
        allowed_mimes = ["application/pdf", "text/plain"]

        if mime_type not in allowed_mimes:
            await message.answer(
                "❌ **Непідтримуваний формат файлу!**\n\n"
                "Будь ласка, надішліть резюме у форматі **PDF** або **TXT** (або введіть **pass** для пропуску)."
            )
            return

        telegram_file = await bot.get_file(doc.file_id)
        file_buffer = await bot.download_file(telegram_file.file_path)
        file_bytes = file_buffer.read()

        if len(file_bytes) > MAX_FILE_SIZE:
            await message.answer(
                f"❌ **Файл перевищує ліміт у {MAX_FILE_SIZE_MB} МБ!** Будь ласка, завантажте менший файл."
            )
            return

        await state.update_data(
            cv_bytes=file_bytes,
            cv_filename=doc.file_name or "cv.pdf",
            cv_mime=mime_type,
        )

    elif message.text and message.text.lower().strip() == "pass":
        await state.update_data(cv_bytes=None, cv_filename=None, cv_mime=None)
    else:
        await message.answer(
            "⚠️ Будь ласка, надішліть **документ** (PDF/TXT до 2 МБ) або введіть **pass**."
        )
        return

    await _render_and_send_preview(message, state, user_data)


async def _render_and_send_preview(
        message: Message, state: FSMContext, user_data: dict
) -> None:
    """Допоміжна функція для перевірки наявності фільтрів та відправки прев'ю."""
    raw_data = await state.get_data()

    has_filters = (
            bool(raw_data.get("include_keywords"))
            or bool(raw_data.get("exclude_keywords"))
            or bool(raw_data.get("query_text"))
    )

    if not has_filters:
        username = user_data.get("username") or message.from_user.first_name

        await message.answer(
            "⚠️ **Помилка створення профілю**\n\n"
            "Ви не ввели жодного фільтра пошуку (скрізь вказали `pass`).\n\n"
            f"🗣 _«Все хуйня, {username}, давай по новой.»_\n\n"
            "🔄 Повертаємось на початок.",
            parse_mode="Markdown",
        )

        await state.set_data({})
        await state.set_state(Profile.name)

        await message.answer(
            "📝 **Введіть ім'я для нового профілю пошуку**\n\n"
            "💡 Ви можете створити кілька різних профілів (наприклад: *Python Junior*, *Data Analyst*).\n\n"
            "⚠️ **Важливо:** якщо ввести назву профілю, який уже існує, новий профіль перезапише старий!"
        )
        return

    inc_words = ", ".join(raw_data.get("include_keywords", [])) or "не вказано"
    exc_words = ", ".join(raw_data.get("exclude_keywords", [])) or "не вказано"
    ai_prompt = raw_data.get("query_text") or "не вказано"

    cv_filename = raw_data.get("cv_filename")
    cv_status = (
        f"📄 <code>{html.escape(cv_filename)}</code>"
        if raw_data.get("cv_bytes") and cv_filename
        else "не додано ❌"
    )

    preview_text = (
        f"📊 <b>Попередній перегляд профілю:</b>\n\n"
        f"🔹 <b>Ім'я профілю:</b> {html.escape(raw_data.get('name', ''))}\n"
        f"➕ Шукати слова: <code>{html.escape(inc_words)}</code>\n"
        f"➖ Ігнорувати слова: <code>{html.escape(exc_words)}</code>\n"
        f"🤖 AI-промпт: <i>{html.escape(ai_prompt)}</i>\n"
        f"📎 Резюме (CV): {cv_status}"
    )

    await message.reply(
        text=preview_text, reply_markup=save_or_remake_profile_kb, parse_mode="HTML"
    )


# ---------------------------------------------------------------------------
# Збереження профілю та перегляд списку профілів (Callback Handlers)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "save_profile")
async def save_profile(
        callback: CallbackQuery, state: FSMContext, user_data: dict, db: AsyncClient
) -> None:
    """Save the constructed FSM profile into the Supabase database."""
    profile_data = await state.get_data()

    if not profile_data:
        await callback.answer("Дані втрачено ❌", show_alert=True)
        await callback.message.edit_text(
            "⚠️ Дані профілю не заповнені або втрачені через неактивність.\n"
            "Будь ласка, почніть заповнення анкети спочатку.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[to_main_button]])
        )
        return
    profile_data["user_id"] = user_data.get("id")

    try:
        await create_or_update_profile_db(profile_data=profile_data, db=db)
        await state.clear()

        # Редагуємо поточне повідомлення-прев'ю на «Головне меню»
        await callback.message.edit_text(
            text="Профіль фільтрації збережено ✅\n\n🏠 **Головне меню**",
            reply_markup=registered_kb,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error("Помилка збереження профілю в БД: %s", e, exc_info=True)
        await callback.message.answer(
            "Сталася помилка бази даних при збереженні профілю."
        )

    await callback.answer()


@router.callback_query(F.data == "show_profiles")
async def show_profiles(
        callback: CallbackQuery, user_data: UserCacheItem, db: AsyncClient
) -> None:
    """Fetch and display all search profiles in a single edited message frame."""
    try:
        profiles_list: list[dict[str, Any]] = await get_user_profiles_from_db(
            user_db_id=user_data.get("id"), db=db
        )

        # Формуємо текст та кнопки для всіх профілів у 1 повідомлення
        text, kb = _build_profiles_view(profiles_list)

        await callback.message.edit_text(
            text=text,
            reply_markup=kb,
            parse_mode="Markdown"
        )
        await callback.answer()

    except EmptyResponse:
        await callback.message.edit_text(
            text="У вас поки немає жодного профілю 📭",
            reply_markup=create_profile_kb
        )
        await callback.answer()
    except Exception as e:
        logger.error("Помилка при отриманні профілів з БД: %s", e, exc_info=True)
        await callback.message.edit_text(
            text="❌ Помилка завантаження даних з бази даних.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[to_main_button]])
        )
        await callback.answer()


@router.callback_query(F.data.startswith("delete_profile:"))
async def handle_delete_profile(callback: CallbackQuery, user_data: UserCacheItem, db: AsyncClient):
    """Delete a specific search profile from DB and update the profiles message in-place."""
    profile_id = int(callback.data.split(":")[1])

    try:
        await delete_profile_from_db(profile_id=profile_id, db=db)
        await callback.answer("Профіль успішно видалено!", show_alert=False)

        # Перевіряємо та отримуємо оновлений список профілів
        profiles_list = await get_user_profiles_from_db(
            user_db_id=user_data.get("id"), db=db
        )
        text, kb = _build_profiles_view(profiles_list)

        # Оновлюємо це ж повідомлення з новим списком профілів
        await callback.message.edit_text(
            text=text,
            reply_markup=kb,
            parse_mode="Markdown"
        )

    except EmptyResponse:
        # Якщо видалили ОСТАННІЙ профіль — виводимо стан з кнопкою "Створити"
        await callback.message.edit_text(
            text="🗑 Профіль видалено. У вас більше немає збережених профілів.",
            reply_markup=create_profile_kb
        )
    except Exception as e:
        logger.error("Помилка видалення профілю %s: %s", profile_id, e, exc_info=True)
        await callback.answer(
            "Не вдалося видалити профіль через помилку БД.", show_alert=True
        )


# ---------------------------------------------------------------------------
# Системні хендлери навігації та відписки
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "to_main")
async def to_main(callback: CallbackQuery) -> None:
    """Redirect user UI back to the main menu in-place."""
    await callback.message.edit_text(
        text="🏠 **Головне меню**",
        reply_markup=registered_kb,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "unsubscribe")
async def unsubscribe(callback: CallbackQuery):
    """Prompt user for confirmation before deleting subscription."""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[delete_subscription_button], [to_main_button]]
    )
    await callback.message.edit_text(
        text="Ви впевнені, що хочете скасувати підписку?", reply_markup=kb
    )
    await callback.answer(
        text="⚠️ УВАГА! Натиснувши 'Видалити', будуть видалені всі ваші профілі пошуку та знайдені вакансії!",
        show_alert=True,
    )


@router.callback_query(F.data == "delete_subscription")
async def delete_subscription(
        callback: CallbackQuery, users_cache: dict, user_data: dict, db: AsyncClient
) -> None:
    """Permanently delete user record from database and clear local RAM cache."""
    user_db_id = user_data.get("id")
    tg_user_id = callback.from_user.id
    users_cache.pop(tg_user_id, None)

    try:
        await delete_user_from_db(user_id=user_db_id, db=db)
        await callback.message.edit_text(
            "Ваш профіль та підписку успішно видалено. Дякуємо, що були з нами!"
        )
        logger.info(
            "Користувач TG:%s (DB:%s) видалив підписку.", tg_user_id, user_db_id
        )
    except Exception as e:
        logger.error(
            "Помилка при видаленні користувача %s з БД: %s",
            user_db_id,
            e,
            exc_info=True,
        )
        await callback.message.edit_text(
            "Сталася помилка при видаленні з бази даних.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[to_main_button]])
        )
    await callback.answer()
