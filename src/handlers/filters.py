from urllib import response

from aiogram import Router, F
from aiogram.filters import Command, callback_data
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup

from supabase import AsyncClient, create_async_client

from src.handlers.crud import register_user_db, create_include_db
from src.keyboards.keyboards import registered_kb

router = Router()


class Include(StatesGroup):
    key_words: list[str] = State()


@router.callback_query(F.data == "include_filter")
async def include_filters(callback: CallbackQuery, state: FSMContext):
    print("start in include_filter")
    await state.set_state(Include.key_words)
    await callback.message.answer("Введіть набір слів через пробіл. "
                                     "При пошуку вакансій буде перевірятися,"
                                     " що хоча в одне слово в цьому наборі є у назві вакансії")

@router.message(Include.key_words)
async def set_include_filter(message: Message, db: AsyncClient, state: FSMContext):
    print("start in set_include_filter")
    text= message.text
    key_words = text.lower().strip().split()
    await state.update_data(key_words=key_words)
    await state.clear()
    user_id = message.from_user.id
    try:
        await create_include_db(user_id=user_id, filters=key_words, db=db)
    except Exception as e:
        raise e


