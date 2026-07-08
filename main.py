"""The main module for launching a Telegram bot.

This module is responsible for initializing the bot, manager, asynchronous client
Supabase, registration of middlewares, routers, and running the Long Polling process.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from supabase import AsyncClient, create_async_client

from render_ping import hack_render
from settings import IN_DOCKER, SUPABASE_KEY, SUPABASE_URL, TELEGRAM_BOT_TOKEN, setup_logging
from src.handlers import router
from src.middlewares.supabase import SupabaseMiddleware
from src.middlewares.user import UserInjectedMiddleware


setup_logging()
logger = logging.getLogger(__name__)

# Ініціалізація бота та диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

async def on_startup(dispatcher: Dispatcher) -> None:
    """Actions performed when the bot starts.

    Initializes the asynchronous Supabase client, registers middleware
    and integrates the client into the global context of the dispatcher.
    """
    logger.info("Запуск бота та ініціалізація ресурсів...")

    # Ініціалізація клієнта Supabase
    supabase_client: AsyncClient = await create_async_client(
        SUPABASE_URL, SUPABASE_KEY
    )

    # Зберігаємо клієнт у workflow_data диспетчера, щоб він був доступний усюди
    dispatcher["supabase_client"] = supabase_client

    # Реєстрація мідлварів (передаємо клієнт із контексту)
    dispatcher.update.middleware(SupabaseMiddleware(supabase_client))
    dispatcher.update.middleware(UserInjectedMiddleware(supabase_client))

    # Включення головного роутера з хендлерами
    dispatcher.include_routers(router)

    # Тригер для утримання Render-сервісу в активному стані (якщо в Docker)
    if IN_DOCKER:
        logger.info("Виявлено середовище Docker. Запуск hack_render()...")
        await hack_render()


async def on_shutdown(dispatcher: Dispatcher) -> None:
    """Дії, що виконуються під час зупинки бота.

    Безпечно закриває всі відкриті з'єднання та сесії клієнта Supabase.
    """
    logger.info("Зупинка бота. Очищення ресурсів...")
    supabase_client: AsyncClient = dispatcher.get("supabase_client")

    if supabase_client:
        # Безпечне закриття HTTP-клієнта Supabase
        if (
            hasattr(supabase_client, "http_client")
            and supabase_client.http_client
        ):
            await supabase_client.http_client.aclose()
            logger.info("Сесію Supabase клієнта успішно закрито.")


async def main() -> None:
    """Головна функція для конфігурації та запуску Long Polling."""
    # Реєстрація колбеків життєвого циклу
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        # Запуск отримання оновлень від Telegram (пропускаємо старі апдейти для чистих логів)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.critical(f"Критична помилка під час роботи бота: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот зупинений користувачем.")



#
#
#
# async def main():
#     # Ініціалізація клієнта
#     supabase_client: AsyncClient = await create_async_client(SUPABASE_URL, SUPABASE_KEY)
#
#     # Реєстрація мідлваря
#     dp.update.middleware(SupabaseMiddleware(supabase_client))
#     dp.update.middleware(UserInjectedMiddleware(supabase_client))
#
#     dp.include_routers(router)
#
#     if IN_DOCKER:
#         await hack_render()
#
#     try:
#         await dp.start_polling(bot)
#     finally:
#         if hasattr(supabase_client, "http_client") and supabase_client.http_client:
#             await supabase_client.http_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())