from aiogram import Router, F
from aiogram.types import CallbackQuery

from supabase import AsyncClient

from src.db.crud import get_user_vacancies_from_db
from src.keyboards.keyboards import registered_kb

router = Router()

@router.callback_query(F.data == "vacancy")
async def my_vac(callback: CallbackQuery, db: AsyncClient, user_data:dict):
    try:
        vacancies = await get_user_vacancies_from_db(user_db_id=user_data['id'], db=db)
        if not vacancies:
            text = "У вас поки немає збережених вакансій."
        else:
            urls = [row["url"] for row in vacancies]
            text = "\n".join(urls)
        await callback.message.answer(text=text, reply_markup=registered_kb)

    except Exception as e:
        print(f"Помилка бази даних: {e}")
        # Тут краще змінити текст помилки, бо ми вже не зберігаємо, а отримуємо дані
        await callback.message.answer("Упс, сталася помилка при отриманні вакансій з БД.")