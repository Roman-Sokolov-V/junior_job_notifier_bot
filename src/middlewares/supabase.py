""""Middleware for integration with external services.

This module contains middleware for aiogram,
which provides access to the Supabase database client inside handlers.
"""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from supabase import AsyncClient

class SupabaseMiddleware(BaseMiddleware):
    """Middleware to wake up an asynchronous Supabase client into the context of a request.

    Adds the initialized AsyncClient object to the 'data' dictionary under the 'db' key,
    which makes it available in all subsequent middleware and handlers.
    """
    def __init__(self, supabase_client: AsyncClient):
        """Initializes the middleware with the Supabase client ready-made.

        Args:
            supabase_client (AsyncClient): Initialized asynchronous
                Supabase client.
        """
        super().__init__()
        self.supabase = supabase_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Обробка вхідного оновлення.

        Впроваджує клієнт Supabase в дані контексту та передає керування
        наступному обробнику.
        """
        # Передаємо готовий асинхронний клієнт у хендлер
        data["db"] = self.supabase
        return await handler(event, data)