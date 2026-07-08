import asyncio
from pprint import pprint
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
#from aiohttp import web
from aiogram.types import Message
from supabase import AsyncClient, create_async_client

from render_ping import hack_render
from settings import SUPABASE_URL, SUPABASE_KEY, TELEGRAM_BOT_TOKEN, IN_DOCKER
from src.middlewares.supabase import SupabaseMiddleware
from src.handlers import start_router, not_registered_user_router, filters_router, vacancies_router
from src.middlewares.user import UserInjectedMiddleware

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(Command("me"))
async def cmd_me(message: Message):
    pprint(message.model_dump(exclude_none=True))
    await message.reply(
        text=f"user_name: {message.from_user.username} \n"
             f"first_name: {message.from_user.first_name} \nlast_name: {message.chat.last_name} \n"
             f"id: {message.from_user.id} \n"
             f"language_code: {message.from_user.language_code}"
             f"is_bot: {message.from_user.is_bot}"

    )


# async def handle_ping(request):
#     """Пінгує для безкоштовної роботи на render.com"""
#     return web.Response(text="Bot is running!")

async def main():
    # Ініціалізація клієнта
    supabase_client: AsyncClient = await create_async_client(SUPABASE_URL, SUPABASE_KEY)

    # Реєстрація мідлваря
    dp.update.middleware(SupabaseMiddleware(supabase_client))
    dp.update.middleware(UserInjectedMiddleware(supabase_client))

    dp.include_routers(start_router, not_registered_user_router, filters_router, vacancies_router)

    if IN_DOCKER:
        await hack_render()

        # # --- ХАК ДЛЯ БЕЗКОШТОВНОГО RENDER ---
        # app = web.Application()
        # app.router.add_get("/", handle_ping)
        # runner = web.AppRunner(app)
        # await runner.setup()
        # # Render сам передає порт у змінну оточення PORT (за замовчуванням 10000)
        # port = int(os.getenv("PORT", 10000))
        # site = web.TCPSite(runner, "0.0.0.0", port)
        # await site.start()
        # print(  # render_port_log
        #     f"Веб-сервер заглушки запущено на порту {port}"
        # )
        # # -------------------------------------
        # print("Бот запускається в контейнері в режимі Polling на Render (Free)...")
    try:
        await dp.start_polling(bot)
    finally:
        if hasattr(supabase_client, "http_client") and supabase_client.http_client:
            await supabase_client.http_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())