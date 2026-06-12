NEXA CLOUD ONE MESSAGE UI BOT

Run:
pip install -r requirements.txt
python bot.py

Edit bot.py:
BOT_TOKEN = "your token"
ADMIN_ID = your telegram id

Important UI fix:
This version uses edit_message_text for menu pages, so old menu messages are edited instead of sending many stacked menu messages.
