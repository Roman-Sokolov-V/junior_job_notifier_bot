import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from supabase import AsyncClient, create_async_client

from settings import SUPABASE_KEY, SUPABASE_URL, TELEGRAM_BOT_TOKEN, setup_logging, WEBHOOK_SECRET, WEBHOOK_URL
from src.handlers import router
from src.middlewares.supabase import SupabaseMiddleware
from src.middlewares.user import UserInjectedMiddleware


setup_logging()
logger = logging.getLogger(__name__)



supabase_client: AsyncClient | None = None

def create_bot() -> Bot:
    return Bot(token=TELEGRAM_BOT_TOKEN)

def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(router)
    return dp


async def on_startup(dispatcher: Dispatcher, bot: Bot) -> None:
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


async def on_shutdown(bot: Bot) -> None:
    logger.info("Зупинка бота. Очищення ресурсів...")
    #await bot.delete_webhook()

    if supabase_client and hasattr(supabase_client, "http_client"):
        await supabase_client.http_client.aclose()
        logger.info("Сесію Supabase клієнта успішно закрито.")

    await bot.session.close()
    logger.info("Сесію бота успішно закрито.")