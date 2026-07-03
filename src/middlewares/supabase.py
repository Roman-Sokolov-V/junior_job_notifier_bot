from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from supabase import AsyncClient

class SupabaseMiddleware(BaseMiddleware):
    def __init__(self, supabase_client: AsyncClient):
        super().__init__()
        self.supabase = supabase_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Передаємо готовий асинхронний клієнт у хендлер
        data["db"] = self.supabase
        return await handler(event, data)