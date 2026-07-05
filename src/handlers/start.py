from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from supabase import AsyncClient

from src.exeptions import EmptyResponse
from src.handlers.crud import get_user_from_db
from src.keyboards.keyboards import not_registered_kb, registered_kb

router = Router()


@router.message(Command('start'))
async def start(message: Message, db: AsyncClient, user_data: dict | None):
    """
    Сама робота бота полягатиме в тому що користувач пише /start,
     хендлер отримує його телеграм id, перевіряє що він вже є в бд.
    Якщо нема то пропонується зареєструватися, якщо погодився, його id вноситься в бд,
     йому пропонується створити фільтри пошуку вакансій, він вводить - вони записуються в бд.
    Якщо при /start користувач вже в базі, показуються його поточні фільтри і пропонується на вибір,
     змінити фільтри пошуку, показати знайдені вакансії, відписатися.
      """
    if not user_data:
        await message.reply(text="You are not registered. Do you want to register?", reply_markup=not_registered_kb)
    else:
        await message.reply(text=f"Привіт {user_data['username']}", reply_markup=registered_kb)


    # try:
    #     data = await get_user_from_db(user_id, db)
    #     user_db_id = data["id"]
    #     await message.reply(text=f"Привіт {data['username']}", reply_markup=registered_kb)
    # except EmptyResponse:
    #     await message.reply(text="You are not registered. Do you want to register?", reply_markup=not_registered_kb)
    # except Exception as e:
    #     print(f"Помилка бази даних: {e}")
    #     await message.answer("Упс, сталася помилка при отриманні даних про користувача з БД.")
