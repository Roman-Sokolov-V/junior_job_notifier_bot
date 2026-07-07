import os
import asyncio
from pprint import pprint
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from aiogram.types import Message
from supabase import AsyncClient, create_async_client

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

@dp.message(Command("my"))
async def my_vac(message: Message, db: AsyncClient):
    user_id = message.from_user.id
    try:
        # 1. Робимо запит до БД
        response = await db.table("vacancies") \
            .select("url, user_matches!inner(users!inner(telegram_user_id))") \
            .eq("user_matches.users.telegram_user_id", user_id) \
            .execute()
        #print("response", response)
        print("response.data", response.data)
        # 2. Витягуємо тільки рядки URL з результату .data
        urls = [row["url"] for row in response.data]

        # 3. Перевіряємо, чи взагалі знайшли якісь вакансії
        if not urls:
            await message.answer("У вас поки немає збережених вакансій.")
            return

        # 4. Склеюємо їх через кому (або через новий рядок \n для краси)
        await message.answer("\n".join(urls))

    except Exception as e:
        print(f"Помилка бази даних: {e}")
        # Тут краще змінити текст помилки, бо ми вже не зберігаємо, а отримуємо дані
        await message.answer("Упс, сталася помилка при отриманні вакансій з БД.")


# @dp.message()
# async def handle_message(message: types.Message, db: AsyncClient):
#     user_id = message.from_user.id
#     username = message.from_user.username or "anonymous"
#
#     try:
#         # Зберігаємо юзера в Supabase через асинхронний HTTP-клієнт
#         await db.table("users").upsert(
#             {"tg_id": user_id, "username": username},
#             on_conflict="tg_id"
#         ).execute()
#
#         await message.answer(f"Привіт, {username}! Твій ID збережено в Supabase.")
#     except Exception as e:
#         print(f"Помилка бази даних: {e}")
#         await message.answer("Упс, сталася помилка при збереженні в БД.")


async def handle_ping(request):
    """Пінгує для безкоштовної роботи на render.com"""
    return web.Response(text="Bot is running!")

async def main():
    # Ініціалізація клієнта
    supabase_client: AsyncClient = await create_async_client(SUPABASE_URL, SUPABASE_KEY)

    # Реєстрація мідлваря
    dp.update.middleware(SupabaseMiddleware(supabase_client))
    dp.update.middleware(UserInjectedMiddleware(supabase_client))

    dp.include_routers(start_router, not_registered_user_router, filters_router, vacancies_router)

    if IN_DOCKER:
        # --- ХАК ДЛЯ БЕЗКОШТОВНОГО RENDER ---
        app = web.Application()
        app.router.add_get("/", handle_ping)
        runner = web.AppRunner(app)
        await runner.setup()
        # Render сам передає порт у змінну оточення PORT (за замовчуванням 10000)
        port = int(os.getenv("PORT", 10000))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        print(  # render_port_log
            f"Веб-сервер заглушки запущено на порту {port}"
        )
        # -------------------------------------
        print("Бот запускається в контейнері в режимі Polling на Render (Free)...")
    try:
        await dp.start_polling(bot)
    finally:
        if hasattr(supabase_client, "http_client") and supabase_client.http_client:
            await supabase_client.http_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())