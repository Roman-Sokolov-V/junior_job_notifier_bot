from aiogram import Router, F
from aiogram.types import CallbackQuery

from supabase import AsyncClient

from src.db.crud import register_user_db
from src.keyboards.keyboards import create_profile_kb

router = Router()



@router.callback_query(F.data == "register_user")
async def register_user(callback: CallbackQuery, db: AsyncClient, users_cache: dict):
    tg_user_id = callback.from_user.id
    tg_username = callback.from_user.username

    try:
        user_data = await register_user_db(user_id=tg_user_id, username=tg_username, db=db)
        users_cache[tg_user_id] = user_data
    except Exception as e:
        print(f"Помилка бази даних: {e}")
        await callback.answer("Упс, сталася помилка при реєстрації користувача в дб.")
    await callback.message.edit_text("Успішно зареєстровано", reply_markup=create_profile_kb)

