import asyncio
import logging

from settings import setup_logging
from src.bot import create_bot, create_dispatcher, init_resources


setup_logging()
logger = logging.getLogger(__name__)


async def main() -> None:
    dp = create_dispatcher()
    bot = create_bot()

    await init_resources(dp)

    # Знімаємо webhook, інакше Telegram відмовить у getUpdates
    # з помилкою "Conflict: can't use getUpdates method while webhook is active"
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook видалено, старт у режимі polling для локальної розробки")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот зупинений користувачем.")