from supabase import AsyncClient
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from src.exeptions import EmptyResponse
from src.db.crud import get_user_from_db


class UserInjectedMiddleware(BaseMiddleware):
    """
    створює кеш з даними користувачів з бд, передає в контекст

    """
    def __init__(self, db: AsyncClient):
        self.db = db
        self.cache = {}
        # Зберігає self.cache = {
        #                         "tg_id": {
        #                             "id": int,
        #                             "username": str,
        #                           }
        #                       }

    async def __call__(self, handler, event: TelegramObject, data: dict):
        tg_user: User = data.get("event_from_user")
        if tg_user:
            # 1. Перевіряємо, чи є tg_id в кеші
            if tg_user.id in self.cache:
                data["user_data"] = self.cache[tg_user.id]
            else:
                # 2. Якщо в кеші немає — ОДИН раз йдемо в базу
                try:
                    user_data: dict = await get_user_from_db(telegram_user_id=tg_user.id, db=self.db)
                    self.cache[tg_user.id] = user_data
                    data["user_data"] = user_data
                except EmptyResponse:
                    # 3. Юзера немає в базі! Записуємо None
                    self.cache[tg_user.id] = None
                    data["user_data"] = None
        data["users_cache"] = self.cache
        return await handler(event, data)
