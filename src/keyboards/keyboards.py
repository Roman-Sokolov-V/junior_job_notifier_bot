"""Keyboards and inline buttons layout configurations.

This module defines all UI navigation elements, including main menus,
FSM wizards, dynamic multi-profile control buttons, and account management views.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# =====================================================================
# START / AUTHENTICATION KEYBOARDS (Реєстрація та старт)
# =====================================================================

not_registered_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Зареєструватися у боті", callback_data="register_user"
            )
        ]
    ]
)
"""Prompt menu for newly arrived, unregistered users to initiate onboarding."""


registered_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔍 Показати знайдені вакансії", callback_data="vacancy"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔧 Додати / змінити профіль", callback_data="create_profile"
            )
        ],
        [InlineKeyboardButton(text="📋 Мої профілі", callback_data="show_profiles")],
        [
            InlineKeyboardButton(
                text="❌ Видалити підписку", callback_data="unsubscribe"
            )
        ],
    ]
)
"""Main navigation hub dashboard for fully registered users."""


# =====================================================================
# INLINE KEYBOARDS FOR FSM ONBOARDING WIZARD (Створення профілів)
# =====================================================================

save_or_remake_profile_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔧 Текст немножко по-дибильному написаний (переробити)",
                callback_data="create_profile",
            )
        ],
        [
            InlineKeyboardButton(
                text="💾 Все чотко, зберегти профіль!", callback_data="save_profile"
            )
        ],
    ]
)
"""Confirmation dashboard inside the search profile deployment wizard with classic quotes."""

create_profile_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Створити профайл пошуку", callback_data="create_profile"
            )
        ]
    ]
)
"""Fallback placeholder menu when no target profiles exist in the database."""


# =====================================================================
# SHARED REUSABLE SINGLE BUTTONS (Компоненти для динамічних меню)
# =====================================================================

to_main_button = InlineKeyboardButton(
    text="📱 До головного меню", callback_data="to_main"
)
"""Navigation leaf link allowing structural jumps straight back to the landing menu."""

delete_subscription_button = InlineKeyboardButton(
    text="❌ Так я впевнений. Видалити підписку", callback_data="delete_subscription"
)
"""Destructive finality operation button that requests backend record purging."""
