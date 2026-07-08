"""Middleware for high-performance in-memory user data caching.

This module utilizes cachetools to provide an in-memory TTL (Time-To-Live) cache,
minimizing database calls to Supabase while ensuring data freshness.
"""

from typing import Any, Awaitable, Callable, Dict, Optional, TypedDict

from supabase import AsyncClient
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from cachetools import TTLCache

from src.exeptions import EmptyResponse
from src.db.crud import get_user_from_db


class UserCacheItem(TypedDict):
    """Schema for a single user record stored in the cache."""
    id: int        # Внутрішній ID користувача в базі даних Supabase
    username: str  # Юзернейм користувача з Telegram / БД


class UserInjectedMiddleware(BaseMiddleware):
    """Middleware to cache user data directly in the application's RAM.

    Uses a TTL (Time-To-Live) strategy to automatically invalidate cached profiles.

    Cache Structure:
        {
            telegram_id (int): {
                "id": int,
                "username": str
            } | None
        }
    """
    def __init__(self, db: AsyncClient):
        """Initialize the middleware with a bounded TTL cache.

        Args:
            db (AsyncClient): The initialized Supabase async client.
        """
        super().__init__()
        self.db = db
        self.cache: TTLCache[int, Optional[UserCacheItem]] = TTLCache(
            maxsize=1000, ttl=300
        )


    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict
    ) -> Any:
        """Process the update, injecting cached or freshly fetched user data."""
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
