import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the bot/ directory regardless of where the script is run from
_bot_dir = Path(__file__).parent
load_dotenv(_bot_dir / ".env")

BOT_TOKEN  = os.getenv("BOT_TOKEN")
API_URL    = os.getenv("API_URL", "http://backend:8000/api/v1")
ADMIN_IDS  = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
