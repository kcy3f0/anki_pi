import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        if os.environ.get("FLASK_ENV") == "production":
            raise RuntimeError("生產環境下必須配置 SECRET_KEY 環境變數！")
        SECRET_KEY = "default-dev-secret-key-change-me"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "flashcards.db")
    DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
