import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "planner.db")
    TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Zaporozhye")
    DAILY_REPORT_TIME: str = os.getenv("DAILY_REPORT_TIME", "09:00")

settings = Settings()