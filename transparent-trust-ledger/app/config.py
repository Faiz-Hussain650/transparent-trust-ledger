from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Transparent Trust Ledger"
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    class Config:
        env_file = ".env"
        extra = "ignore"   # 👈 Important: ignores unused .env vars safely

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
