"""
config.py — loads environment variables for SchemeMax AI
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "mediScheme.db")

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@gmail.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")
