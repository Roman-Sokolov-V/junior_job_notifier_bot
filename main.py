# """The main module for launching a Telegram bot.
#
# This module is responsible for initializing the bot, manager, asynchronous client
# Supabase, registration of middlewares, routers, and running the Long Polling process.
# """
# import asyncio
# import logging
#
# from aiogram import Bot, Dispatcher
# from aiogram.fsm.storage.memory import MemoryStorage
# from aiohttp import web
# from supabase import AsyncClient, create_async_client
#
# from render_ping import hack_render
# from settings import IN_DOCKER, SUPABASE_KEY, SUPABASE_URL, TELEGRAM_BOT_TOKEN, setup_logging, WEB_SERVER_HOST, \
#     WEB_SERVER_PORT, WEBHOOK_URL, WEBHOOK_SECRET
#
# from src.handlers import router
# from src.middlewares.supabase import SupabaseMiddleware
# from src.middlewares.user import UserInjectedMiddleware
# from webhook import create_prepared_web_app

# setup_logging()
# logger = logging.getLogger(__name__)
# #
# # Ініціалізація бота та диспетчера
# bot = Bot(token=TELEGRAM_BOT_TOKEN)
# dp = Dispatcher(storage=MemoryStorage())
#
# async def on_startup(dispatcher: Dispatcher) -> None:
#     """Actions performed when the bot starts.
#
#     Initializes the asynchronous Supabase client, registers middleware
#     and integrates the client into the global context of the dispatcher.
#     """
#     global supabase_client
#     logger.info("Запуск бота та ініціалізація ресурсів...")
#
#     # Ініціалізація клієнта Supabase
#     if supabase_client is None:
#         supabase_client: AsyncClient = await create_async_client(
#             SUPABASE_URL, SUPABASE_KEY
#         )
#
#     # Зберігаємо клієнт у workflow_data диспетчера, щоб він був доступний усюди
#     dispatcher["supabase_client"] = supabase_client
#
#     # Реєстрація мідлварів (передаємо клієнт із контексту)
#     dispatcher.update.middleware(SupabaseMiddleware(supabase_client))
#     dispatcher.update.middleware(UserInjectedMiddleware(supabase_client))
#
#     # Включення головного роутера з хендлерами
#     dispatcher.include_routers(router)
#
#     # Тригер для утримання Render-сервісу в активному стані (якщо в Docker)
#     if IN_DOCKER:
#         logger.info("Виявлено середовище Docker. Запуск hack_render()...")
#         await hack_render()
#
#
# async def on_shutdown(dispatcher: Dispatcher) -> None:
#     """Дії, що виконуються під час зупинки бота.
#
#     Безпечно закриває всі відкриті з'єднання та сесії клієнта Supabase.
#     """
#     logger.info("Зупинка бота. Очищення ресурсів...")
#     supabase_client: AsyncClient = dispatcher.get("supabase_client")
#
#     if supabase_client:
#         # Безпечне закриття HTTP-клієнта Supabase
#         if (
#             hasattr(supabase_client, "http_client")
#             and supabase_client.http_client
#         ):
#             await supabase_client.http_client.aclose()
#             logger.info("Сесію Supabase клієнта успішно закрито.")
#
#
# async def main() -> None:
#     """Головна функція для конфігурації та запуску Long Polling."""
#     # Реєстрація колбеків життєвого циклу
#     dp.startup.register(on_startup)
#     dp.shutdown.register(on_shutdown)
#
#     try:
#         # Запуск отримання оновлень від Telegram (пропускаємо старі апдейти для чистих логів)
#         await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
#     except Exception as e:
#         logger.critical(f"Критична помилка під час роботи бота: {e}", exc_info=True)
#
#
# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except (KeyboardInterrupt, SystemExit):
#         logger.info("Бот зупинений користувачем.")



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


# if __name__ == "__main__":
#     asyncio.run(main())

#
# async def main() -> None:
#     """Головна функція для конфігурації та запуску Long Polling."""
#     logger.info("Запуск бота та ініціалізація ресурсів...")
#
#     # 1. Ініціалізація клієнтів
#     bot = Bot(token=TELEGRAM_BOT_TOKEN)
#     dp = Dispatcher(storage=MemoryStorage())
#
#     supabase_client: AsyncClient = await create_async_client(
#         SUPABASE_URL, SUPABASE_KEY
#     )
#
#     # Зберігаємо клієнт у workflow_data диспетчера, щоб він був доступний у хендлерах
#     dp["supabase_client"] = supabase_client
#
#     # 2. Реєстрація мідлварів (строго ДО старту пулінгу і тільки один раз)
#     dp.update.middleware(SupabaseMiddleware(supabase_client))
#     dp.update.middleware(UserInjectedMiddleware(supabase_client))
#
#     # 3. Включення головного роутера з хендлерами
#     dp.include_routers(router)
#
#     # 4. Тригер для утримання Render-сервісу в активному стані (якщо в Docker)
#     if IN_DOCKER:
#         logger.info("Виявлено середовище Docker. Запуск hack_render()...")
#         # Запускаємо як фонову задачу, щоб вона не блокувала основний потік
#         asyncio.create_task(hack_render())
#
#     try:
#         logger.info("Бот успішно запустився. Починаємо пулінг...")
#         # Запуск отримання оновлень від Telegram
#         await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
#
#     except Exception as e:
#         logger.critical(f"Критична помилка під час роботи бота: {e}", exc_info=True)
#
#     finally:
#         # Безпечне очищення ресурсів у будь-якому випадку (заміна on_shutdown)
#         logger.info("Зупинка бота. Очищення ресурсів...")
#
#         # Закриваємо сесію Supabase
#         if supabase_client and hasattr(supabase_client, "http_client") and supabase_client.http_client:
#             await supabase_client.http_client.aclose()
#             logger.info("Сесію Supabase клієнта успішно закрито.")
#
#         # Закриваємо сесію самого бота aiogram, щоб не було Task pending помилок
#         await bot.session.close()
#         logger.info("Сесію бота успішно закрито.")
#
#
# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except (KeyboardInterrupt, SystemExit):
#         logger.info("Бот зупинений користувачем.")




# async def main() -> None:
#     """Головна функція для конфігурації та запуску Long Polling."""
#     logger.info("Запуск бота та ініціалізація ресурсів...")
#
#     supabase_client: AsyncClient = await create_async_client(
#         SUPABASE_URL, SUPABASE_KEY
#     )
#     bot = create_bot()
#     dp = create_dispatcher(supabase_client)
#     app = create_prepared_web_app(bot, dp)
#     web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT) #, ssl_context=context)
#
#     # # 4. Тригер для утримання Render-сервісу в активному стані (якщо в Docker)
#     # if IN_DOCKER:
#     #     logger.info("Виявлено середовище Docker. Запуск hack_render()...")
#     #     # Запускаємо як фонову задачу, щоб вона не блокувала основний потік
#     #     asyncio.create_task(hack_render())
#
#     try:
#         logger.info("Бот успішно запустився. Починаємо пулінг...")
#         # Запуск отримання оновлень від Telegram
#         await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
#
#     except Exception as e:
#         logger.critical(f"Критична помилка під час роботи бота: {e}", exc_info=True)
#
#     finally:
#         # Безпечне очищення ресурсів у будь-якому випадку (заміна on_shutdown)
#         logger.info("Зупинка бота. Очищення ресурсів...")
#
#         # Закриваємо сесію Supabase
#         if supabase_client and hasattr(supabase_client, "http_client") and supabase_client.http_client:
#             await supabase_client.http_client.aclose()
#             logger.info("Сесію Supabase клієнта успішно закрито.")
#
#         # Закриваємо сесію самого бота aiogram, щоб не було Task pending помилок
#         await bot.session.close()
#         logger.info("Сесію бота успішно закрито.")
#
#
# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except (KeyboardInterrupt, SystemExit):
#         logger.info("Бот зупинений користувачем.")
#import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from supabase import AsyncClient, create_async_client

from settings import SUPABASE_KEY, SUPABASE_URL, TELEGRAM_BOT_TOKEN, setup_logging, WEBHOOK_SECRET
from src.handlers import router
from src.middlewares.supabase import SupabaseMiddleware
from src.middlewares.user import UserInjectedMiddleware


setup_logging()
logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/webhook"

# Render автоматично прописує публічну адресу сервісу
# у змінну оточення RENDER_EXTERNAL_URL, наприклад:
# https://junior-job-notifier-bot.onrender.com
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "") + WEBHOOK_PATH

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

dp.include_routers(router)

supabase_client: AsyncClient | None = None


async def on_startup(dispatcher: Dispatcher) -> None:
    """"Called once when the aiohttp server starts."""
    global supabase_client
    logger.info("Запуск бота та ініціалізація ресурсів...")

    if supabase_client is None:
        supabase_client = await create_async_client(SUPABASE_URL, SUPABASE_KEY)
        dispatcher["supabase_client"] = supabase_client
        dispatcher.update.middleware(SupabaseMiddleware(supabase_client))
        dispatcher.update.middleware(UserInjectedMiddleware(supabase_client))

    await bot.set_webhook(
        WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        allowed_updates=dispatcher.resolve_used_update_types(),
    )
    logger.info(f"Webhook встановлено: {WEBHOOK_URL}")


async def on_shutdown(dispatcher: Dispatcher) -> None:
    """Called when the server is stopped (for example, by SIGTERM)."""
    logger.info("Зупинка бота. Очищення ресурсів...")
    await bot.delete_webhook()
    if supabase_client and hasattr(supabase_client, "http_client"):
        await supabase_client.http_client.aclose()
        logger.info("Сесію Supabase клієнта успішно закрито.")


def main() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот зупинений користувачем.")