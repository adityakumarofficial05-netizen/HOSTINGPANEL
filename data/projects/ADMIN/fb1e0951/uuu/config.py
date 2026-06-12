import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_SECRET_COMMAND = "/admin_x_danger_2024"
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_ID", "0"))

# Domain & Email
DOMAIN = os.getenv("DOMAIN", "")

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Webhook
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Database
DATABASE = "x_danger.db"

# Payment
FAMPAY_PAYMENT_LINK = os.getenv("FAMPAY_PAYMENT_LINK")
