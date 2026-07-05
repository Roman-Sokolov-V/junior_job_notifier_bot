import os
import dotenv

dotenv.load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SICRET_KEY") #SUPABASE_PUPLISH_KEY

IN_DOCKER = os.getenv("IN_DOCKER", False)