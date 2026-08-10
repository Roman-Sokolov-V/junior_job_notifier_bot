import logging

from supabase import AsyncClient

from src.db.storage import upload_file
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
    """deletes the profile from the database and the cv file from the storage"""
    # 1. Отримуємо дані про профіль, щоб дізнатися шлях до файлу
    response = await (
        db.table("user_profiles")
        .select("cv_file")
        .eq("id", profile_id)
        .maybe_single()
        .execute()
    )

    if not response.data:
        raise EmptyResponse("Профіль не знайдено.")

    cv_file_path = response.data.get("cv_file")

    # 2. Якщо файл є в Storage — видаляємо його
    if cv_file_path:
        try:
            bucket_name, storage_path = cv_file_path.split("/", maxsplit=1)

            await db.storage.from_(bucket_name).remove([storage_path])
            logger.info("Файл %s успішно видалено зі Storage", cv_file_path)
        except Exception as e:
            logger.error("Помилка видалення файлу зі Storage: %s", e, exc_info=True)

    # 3. Видаляємо сам запис профілю з таблиці БД
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
    # Витягуємо дані CV
    cv_bytes = profile_data.pop("cv_bytes", None)
    cv_filename = profile_data.pop("cv_filename", None)
    cv_mime = profile_data.pop("cv_mime", None)
    # Спочатку створюємо/оновлюємо профіль у БД
    response = await (
        db.table("user_profiles")
        .upsert(
            profile_data,
            on_conflict="user_id,name",
        )
        .execute()
    )

    if not response.data:
        raise Exception("Не вдалося створити профіль у БД.")

    created_profile = response.data[0]
    profile_id = created_profile["id"]

    # Якщо є файл CV — завантажуємо його у Storage
    if cv_bytes and cv_filename:
        storage_path = f"{profile_id}/{cv_filename}"
        storage_response = await upload_file(
            db=db,
            file_bytes=cv_bytes,
            destination_path=storage_path
        )

        # Якщо завантаження пройшло успішно — оновлюємо поля в БД
        if storage_response:
            logger.info(storage_response)

            storage_full_path = storage_response.full_path
            logger.info(storage_full_path)
            update_response = await (
                db.table("user_profiles")
                .update({
                    "cv_file": storage_full_path,
                    "mime_type": cv_mime
                })
                .eq("id", profile_id)
                .execute()
            )
            return update_response.data[0]

    return created_profile


async def get_user_vacancies_from_db(user_db_id: int, db: AsyncClient) -> list[dict]:
    response = await (
        db.table("vacancies")
        .select("title, url, user_matches!inner(user_id)")
        .eq("user_matches.user_id", user_db_id)
        .execute()
    )
    return response.data
