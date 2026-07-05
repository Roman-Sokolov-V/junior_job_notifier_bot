from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

registered_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Створити (поміняти) include фільтри", callback_data="include_filter")],
        # [InlineKeyboardButton(text="Створити (поміняти) exclude фільтри", callback_data="exclude_filter")],
        # [InlineKeyboardButton(text="Створити (поміняти) промпт", callback_data="prompt_filter")],
        # [InlineKeyboardButton(text="Показати знайдені вакансії", callback_data="vacancy")],
        # [InlineKeyboardButton(text="Видалити підписку", callback_data="unsubscribe")],
    ]
)

not_registered_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Зареєструватися", callback_data="register_user"),
        ]
    ]
)