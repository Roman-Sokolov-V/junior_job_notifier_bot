import logging
import os

from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from settings import setup_logging, WEBHOOK_SECRET, WEBHOOK_PATH
from src.bot import create_dispatcher, on_startup, on_shutdown, create_bot

setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    dp = create_dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    bot = create_bot()
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(
        app, path=WEBHOOK_PATH
    )
    setup_application(app, dp, bot=bot)
    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt, SystemExit:
        logger.info("Бот зупинений користувачем.")
