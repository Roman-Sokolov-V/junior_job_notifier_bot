import os
import logging.config

import dotenv


dotenv.load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SICRET_KEY") #SUPABASE_PUPLISH_KEY

IN_DOCKER = os.getenv("IN_DOCKER", False)

LOG_LEVEL = "INFO" if IN_DOCKER else "DEBUG"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "render_standard": {
            # Формат оптимізовано під Render: виводимо ім'я модуля, де стався запис, та рядок коду
            "format": "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "render_standard",
            "stream": "ext://sys.stdout",  # Явно вказуємо стандартний вивід
        },
    },
    "loggers": {
        "": {  # Корневий логер для всього проєкту
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
        # Заглушаємо занадто детальні логи сторонніх бібліотек, які можуть спамити
        "aiogram": {
            "level": "INFO",
            "propagate": True,
        },
        "httpx": {  # Важливо для Supabase, бо він працює через httpx
            "level": "WARNING",  # Щоб не бачити кожен HTTP-запит до БД у логах Render
            "propagate": True,
        },
    },
}

def setup_logging():
    """Ініціалізація конфігурації логування для Docker/Render."""
    logging.config.dictConfig(LOGGING_CONFIG)
