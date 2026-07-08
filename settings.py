import os
import dotenv
import logging

dotenv.load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SICRET_KEY") #SUPABASE_PUPLISH_KEY

IN_DOCKER = os.getenv("IN_DOCKER", False)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
render_ping_logger = logging.getLogger("RenderPing")
bot_logger = logging.getLogger("Bot")