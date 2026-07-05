from supabase import AsyncClient

from src.exeptions import EmptyResponse
#from postgrest.exceptions import APIError

async def get_user_from_db(user_id: int, db: AsyncClient):
    print("Шукаю користувача в бд")
    response = await db.table('users').select("id", "username").eq("telegram_user_id", user_id).execute()
    print(response.data)
    if not response.data:
        raise EmptyResponse
    return response.data[0]





async def register_user_db(user_id: int, username: str, db: AsyncClient):
    response = await (
        db.table("users")
        .insert({"telegram_user_id": user_id, "username": username.strip()})
        .execute()
    )
    print(response.data)
    return response.data[0]





async def create_include_db(user_id: int, filters: list, db: AsyncClient, profile_name: str | None = None):

    # План Б: якщо RPC не спрацював
    print(f"add include filters")
    # 1. Знаходимо внутрішній id користувача в таблиці users
    user_response = await (
        db.table("users")
        .select("id")
        .eq("telegram_user_id", user_id)
        .execute()
    )

    if not user_response.data:
        print(f"Помилка: Користувача з telegram_user_id {user_id} немає в базі.")

        return

    user_db_id = user_response.data[0]["id"]

    # 2. Робимо правильний upsert із зазначенням on_conflict
    payload = {
                "user_id": user_db_id,
                "include_keywords": filters,
            }
    if profile_name:
        payload["name"] = profile_name

    response = await (
        db.table("user_profiles")
        .upsert(
            {
                "user_id": user_db_id,
                "include_keywords": filters,
            },
            on_conflict="user_id,name"  # <--- Ключовий момент!
        )
        .execute()
    )
    print(response.data)