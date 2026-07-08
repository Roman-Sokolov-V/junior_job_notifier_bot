import os
import logging

from aiohttp import web


logger = logging.getLogger(__name__)

# --- ХАК ДЛЯ БЕЗКОШТОВНОГО RENDER ---
# для роботи також потрібне періодичне пінгування сервісу
# у мене реалізовано на cron-job.org
async def handle_ping(request):
    """Пінгує для безкоштовної роботи на render.com"""
    # Цей запис буде з'являтися кожні 10 хвилин, коли cron-job.org смикає бот
    logger.info("🤖 Отримано пінг від cron-job.org! Тримаємо додаток живим.")
    return web.Response(text="OK", status=200)

async def hack_render():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()

    # Render сам передає порт у змінну оточення PORT
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🚀 Веб-сервер заглушки успішно запущено на порту {port}")
# -------------------------------------------------