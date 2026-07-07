from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from supabase import AsyncClient

from src.exeptions import EmptyResponse
from src.handlers.crud import create_or_update_profile_db, get_user_profiles_from_db, delete_profile_from_db, \
    delete_user_from_db
from src.keyboards.keyboards import registered_kb, save_or_remake_profile_kb, create_profile_kb, to_main_button, \
    delete_subscription_button

router = Router()



class Profile(StatesGroup):
    name: str = State()
    exclude_keywords: list = State()
    include_keywords: list = State()
    query_text: str = State()


@router.callback_query(F.data == "create_profile")
async def create_profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    print("start in create_profile")
    await state.set_state(Profile.name)
    await callback.message.answer(
        "📝 **Введіть ім'я для нового профілю пошуку**\n\n"
        "💡 Ви можете створити кілька різних профілів (наприклад: *Python Junior*, *Data Analyst*).\n\n"
        "⚠️ **Важливо:** якщо ввести назву профілю, який уже існує, новий профіль перезапише старий!"
    )
@router.message(Profile.name)
async def add_name_ask_for_include_filters(message: Message, state: FSMContext):
    print("start add_name_ask_for_include_filters")
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
async def add_include_ask_for_exclude_filters(message: Message, state: FSMContext):
    print("start add_include_ask_for_exclude_filters")
    text = message.text
    key_words = text.lower().strip().split()
    await state.update_data(include_keywords=key_words if key_words != ["pass"] else [])
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
async def add_exclude_ask_for_prompt(message: Message, state: FSMContext):
    print("start add_exclude_ask_for_prompt")
    text = message.text
    key_words = text.lower().strip().split()
    await state.update_data(exclude_keywords=key_words if key_words != ["pass"] else [])
    await state.set_state(Profile.query_text)
    await message.answer(
        "🤖 **Налаштування AI-фільтра (аналіз вакансії за допомогою ШІ)**\n\n"
        "Опишіть своїми словами, що саме нейромережа має шукати або перевіряти в повному описі вакансії.\n"
        "_(Наприклад: «Відсіюй вакансії, де вимагають знання англійської вище B1» або «Шукай тільки позиції з можливістю повного ремонтауту»)_\n\n"
        "⏩ Якщо цей фільтр не потрібен, просто введіть **pass**",
        parse_mode="Markdown"
    )

@router.message(Profile.query_text)
async def add_prompt_create_profile_in_db(message: Message, state: FSMContext, user_data: dict):
    print("start in add_prompt_create_profile_in_db")
    text = message.text.strip()
    await state.update_data(query_text=text if text.lower() != "pass" else "")
    profile_data = await state.get_data()
    #await state.clear()

    profile_name = profile_data.pop("name")
    if not any(profile_data.values()):
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
    profile_data["name"] = profile_name
    profile_data["user_id"] = user_data.get("id")

    inc_words = ", ".join(profile_data.get('include_keywords', [])) or "не вказано"
    exc_words = ", ".join(profile_data.get('exclude_keywords', [])) or "не вказано"
    ai_prompt = profile_data.get('query_text') or "не вказано"

    await message.reply(
        text=f"📊 **Попередній перегляд профілю:**\n\n"
             f"🔹 **Ім'я профілю:** {profile_data['name']}\n"
             f"➕ Шукати слова: `{inc_words}`\n"
             f"➖ Ігнорувати слова: `{exc_words}`\n"
             f"🤖 AI-промпт: *{ai_prompt}*",
        reply_markup=save_or_remake_profile_kb,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "save_profile")
async def save_profile(callback: CallbackQuery, state: FSMContext, user_data: dict, db: AsyncClient):
    profile_data = await state.get_data()
    await state.clear()
    profile_data["user_id"] = user_data.get("id")

    try:
        await create_or_update_profile_db(profile_data=profile_data, db=db)
        await callback.message.answer("Профіль фільтрації збережено")
        await callback.message.answer(text=f"Головне меню", reply_markup=registered_kb)
    except Exception as e:
        await callback.message.answer(f"Database error {e}")

@router.callback_query(F.data == "show_profiles")
async def show_profiles(callback: CallbackQuery, user_data: dict, db: AsyncClient):
    try:
        profiles_list = await get_user_profiles_from_db(user_db_id=user_data.get("id"), db=db)

        # Використовуємо enumerate, щоб знати індекс поточного профілю
        for index, profile in enumerate(profiles_list):

            # Базова кнопка видалення (перший рядок клавіатури)
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
        await callback.message.answer(text="У вас поки нема жодного профілю",reply_markup=create_profile_kb)
    except Exception as e:
        await callback.message.answer(f"Database error {e}")



@router.callback_query(F.data.startswith("delete_profile:"))
async def handle_delete_profile(callback: CallbackQuery, db: AsyncClient):
    # Дістаємо ID профілю з callback_data (розбиваємо рядок по двокрапці)
    profile_id = int(callback.data.split(":")[1])

    try:
        # 1. Видаляємо з бази даних
        await delete_profile_from_db(profile_id=profile_id, db=db)

        # 2. Сповіщаємо користувача віконцем що спливає
        await callback.answer("Профіль успішно видалено!", show_alert=False)

        # 3. Візуальний ефект: замість тексту профілю пишемо, що його видалено
        await callback.message.edit_text("🗑 Цей профіль було видалено.")

    except Exception as e:
        print(f"Помилка видалення: {e}")
        await callback.answer("Не вдалося видалити профіль через помилку БД.", show_alert=True)

@router.callback_query(F.data == "to_main")
async def to_main(callback: CallbackQuery):
    await callback.message.edit_text(text="Головне меню", reply_markup=registered_kb)


@router.callback_query(F.data == "unsubscribe")
async def unsubscribe(callback: CallbackQuery):

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [delete_subscription_button],
            [to_main_button]
        ]
    )
    # 1. Змінюємо кнопки та текст у чаті (без show_alert)
    await callback.message.edit_text(
        text="Ви впевнені, що хочете скасувати підписку?",
        reply_markup=kb
    )

    # 2. А ось ТУТ запускаємо модальне вікно-попередження!
    await callback.answer(
        text="⚠️ УВАГА! Натиснувши 'Видалити', будуть видалені всі ваші профілі пошуку та знайдені вакансії!",
        show_alert=True
    )


@router.callback_query(F.data == "delete_subscription")
async def delete_subscription(callback: CallbackQuery, users_cache: dict, user_data: dict, db: AsyncClient):
    user_db_id = user_data.get("id")
    tg_user_id = callback.from_user.id
    #remove from cache
    users_cache.pop(tg_user_id, None)
    #remove from db
    try:
        await delete_user_from_db(user_id=user_db_id, db=db)
        await callback.message.edit_text("Ваш профіль та підписку успішно видалено.")
    except Exception as e:
        print(f"Помилка видалення: {e}")
        await callback.message.edit_text("Сталася помилка при видаленні з бази даних.")
    await callback.answer()

