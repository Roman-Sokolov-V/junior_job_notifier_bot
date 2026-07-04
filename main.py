import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from supabase import AsyncClient, create_async_client

from settings import SUPABASE_URL, SUPABASE_KEY, TELEGRAM_BOT_TOKEN
from src.middlewares.supabase import SupabaseMiddleware


bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(Command("my"))
async def my_vac(message: types.Message, db: AsyncClient):
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


async def main():
    # Ініціалізація клієнта
    supabase_client: AsyncClient = await create_async_client(SUPABASE_URL, SUPABASE_KEY)

    # Реєстрація мідлваря
    dp.update.middleware(SupabaseMiddleware(supabase_client))

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





    print("Бот запускається в режимі Polling на Render (Free)...")
    try:
        await dp.start_polling(bot)
    finally:
        # У самого supabase_client немає close(),
        # але ми можемо закрити внутрішній асинхронний HTTP-клієнт httpx
        if hasattr(supabase_client, "http_client") and supabase_client.http_client:
            await supabase_client.http_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())