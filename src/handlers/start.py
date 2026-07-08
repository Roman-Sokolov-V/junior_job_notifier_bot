from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.keyboards.keyboards import not_registered_kb, registered_kb

router = Router()


@router.message(Command('start'))
async def start(message: Message, user_data: dict | None):
    if not user_data:
        await message.reply(text="You are not registered. Do you want to register?", reply_markup=not_registered_kb)
    else:
        await message.reply(text=f"Привіт {user_data['username']}", reply_markup=registered_kb)

