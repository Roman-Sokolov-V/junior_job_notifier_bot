from pprint import pprint

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("me"))
async def cmd_me(message: Message):
    pprint(message.model_dump(exclude_none=True))
    await message.reply(
        text=f"user_name: {message.from_user.username} \n"
             f"first_name: {message.from_user.first_name} \nlast_name: {message.chat.last_name} \n"
             f"id: {message.from_user.id} \n"
             f"language_code: {message.from_user.language_code}"
             f"is_bot: {message.from_user.is_bot}"

    )
