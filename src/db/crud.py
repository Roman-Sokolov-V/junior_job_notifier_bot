import logging

from supabase import AsyncClient

from src.exceptions import EmptyResponse

logger = logging.getLogger(__name__)


async def get_user_from_db(telegram_user_id: int, db: AsyncClient) -> dict:
    logger.info("Шукаю користувача в бд")
    response = await (
        db.table("users")
        .select("id", "username")
        .eq("telegram_user_id", telegram_user_id)
        .execute()
    )
    logger.debug(response.data)
    if not response.data:
        raise EmptyResponse
    return response.data[0]


async def get_user_profiles_from_db(user_db_id: int, db: AsyncClient) -> list[dict]:
    logger.info("Шукаю profile в бд")
    response = await (
        db.table("user_profiles").select("*").eq("user_id", user_db_id).execute()
    )
    logger.debug(response.data)
    if not response.data:
        raise EmptyResponse
    return response.data


async def delete_profile_from_db(profile_id: int, db: AsyncClient) -> None:
    await db.table("user_profiles").delete().eq("id", profile_id).execute()


async def register_user_db(user_id: int, username: str, db: AsyncClient) -> dict:
    """
    create user
    """
    user = await (
        db.table("users")
        .insert({"telegram_user_id": user_id, "username": username.strip()})
        .execute()
    )
    user_data = user.data[0]
    return user_data


async def delete_user_from_db(user_id: int, db: AsyncClient) -> None:
    await db.table("users").delete().eq("id", user_id).execute()


async def create_or_update_profile_db(profile_data: dict, db: AsyncClient) -> dict:
    response = await (
        db.table("user_profiles")
        .upsert(
            profile_data,
            on_conflict="user_id,name",  # <--- Ключовий момент!
        )
        .execute()
    )
    return response.data[0]


async def get_user_vacancies_from_db(user_db_id: int, db: AsyncClient) -> list[dict]:
    response = await (
        db.table("vacancies")
        .select("title, url, user_matches!inner(user_id)")
        .eq("user_matches.user_id", user_db_id)
        .execute()
    )
    return response.data
