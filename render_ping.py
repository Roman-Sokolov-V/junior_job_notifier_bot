import os
from aiohttp import web
from settings import render_ping_logger as logger

# --- ХАК ДЛЯ БЕЗКОШТОВНОГО RENDER З ЛОГУВАННЯМ ---

async def handle_ping(request):
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