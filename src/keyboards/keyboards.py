from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

registered_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Показати знайдені вакансії", callback_data="vacancy")],
        [InlineKeyboardButton(text="Додати(поміняти) профайл пошуку вакансій", callback_data="create_profile"),],
        [InlineKeyboardButton(text="Мої профілі", callback_data="show_profiles"),],
        [InlineKeyboardButton(text="Видалити підписку", callback_data="unsubscribe")],
    ]
)

not_registered_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Зареєструватися", callback_data="register_user"),
        ]
    ]
)

create_profile_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Створити профайл пошуку вакансій", callback_data="create_profile"),]
    ]
)

update_profile_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Створити (поміняти) include фільтри", callback_data="include_filter")],
        # [InlineKeyboardButton(text="Створити (поміняти) exclude фільтри", callback_data="exclude_filter")],
        # [InlineKeyboardButton(text="Створити (поміняти) промпт", callback_data="prompt_filter")],
        # [InlineKeyboardButton(text="Показати знайдені вакансії", callback_data="vacancy")],
        # [InlineKeyboardButton(text="Видалити підписку", callback_data="unsubscribe")],
    ]
)

save_or_remake_profile_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🤦‍♂️ Просто текст немножко по-дибильному написаний (переробити)",
                callback_data="create_profile"
            )
        ],
        [
            InlineKeyboardButton(
                text="💾 Все чотко, зберегти профіль!",
                callback_data="save_profile"
            )
        ],
    ]
)

to_main_button = InlineKeyboardButton(text="📱 До головного меню", callback_data="to_main")
delete_subscription_button = InlineKeyboardButton(text="❌ Видалити", callback_data="delete_subscription")