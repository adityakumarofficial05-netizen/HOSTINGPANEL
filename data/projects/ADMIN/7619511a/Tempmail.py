#!/usr/bin/env python3
"""
Telegram Temp Mail Bot
----------------------
Uses python-telegram-bot v21+, SQLite, and the free 1secmail.com API.
Deployable on Render with Python 3.14.
"""

import asyncio
import json
import logging
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ========== CONFIGURATION (replace with your own values) ==========
BOT_TOKEN = "8765532236:AAENIXedj8lHa5OjzmZTR1o_Ol8VwsYvIOM"  # Your bot token from @BotFather
ADMIN_ID = 8475663053                 # Your Telegram user ID
# =================================================================

# Database file (will be created automatically)
DB_FILE = "temp_mail_bot.db"

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------- Database helpers ----------
def init_db():
    """Create tables if they don't exist (synchronous, called once at startup)."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS generated_emails (
            email_address TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT,
            last_notified_id INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )
    conn.commit()
    conn.close()

async def db_execute(sql, params=()):
    """Run a write query in a thread to keep the event loop free."""
    def _exec():
        conn = sqlite3.connect(DB_FILE)
        conn.execute(sql, params)
        conn.commit()
        conn.close()
    await asyncio.to_thread(_exec)

async def db_fetchall(sql, params=()):
    """Run a read query returning all rows."""
    def _fetch():
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        conn.close()
        return rows
    return await asyncio.to_thread(_fetch)

async def db_fetchone(sql, params=()):
    """Run a read query returning one row."""
    def _fetch():
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        conn.close()
        return row
    return await asyncio.to_thread(_fetch)

# ---------- 1secmail API helpers (async via thread pool) ----------
API_BASE = "https://www.1secmail.com/api/v1/"

async def api_gen_random_mailbox(count=1):
    """Generate random temporary email addresses."""
    url = f"{API_BASE}?action=genRandomMailbox&count={count}"
    def _req():
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    return await asyncio.to_thread(_req)

async def api_get_messages(login, domain):
    """Fetch inbox for a given email."""
    url = f"{API_BASE}?action=getMessages&login={login}&domain={domain}"
    def _req():
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    return await asyncio.to_thread(_req)

async def api_read_message(login, domain, msg_id):
    """Fetch full content of a message."""
    url = f"{API_BASE}?action=readMessage&login={login}&domain={domain}&id={msg_id}"
    def _req():
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    return await asyncio.to_thread(_req)

# ---------- User helper ----------
async def register_user(user_id: int):
    """Insert user if not present."""
    user = await db_fetchone("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not user:
        await db_execute(
            "INSERT INTO users (user_id, created_at) VALUES (?, ?)",
            (user_id, datetime.now(timezone.utc).isoformat()),
        )

# ---------- Command handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with support button."""
    user = update.effective_user
    await register_user(user.id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Support", url="https://t.me/BOT_CLONER")]
    ])
    await update.message.reply_text(
        "👋 Welcome to the Temp Mail Bot!\n\n"
        "Commands:\n"
        "/create - Generate a new temporary email\n"
        "/list - List your active temp emails\n"
        "/inbox <index> - Check inbox for a specific email\n"
        "/read <index> <msg_id> - Read full message\n"
        "/delete <index> - Delete a temp email\n\n"
        "ℹ️ Limit: 3 emails (unlimited for admins)\n"
        "🔄 Auto‑check every 15 seconds",
        reply_markup=keyboard,
    )

async def create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a new temporary email address."""
    user = update.effective_user
    await register_user(user.id)

    # Check limit for normal users
    if user.id != ADMIN_ID:
        count_row = await db_fetchone(
            "SELECT COUNT(*) as cnt FROM generated_emails WHERE user_id=?", (user.id,)
        )
        if count_row["cnt"] >= 3:
            await update.message.reply_text("❌ You already have 3 active temp emails. Delete one first with /delete.")
            return

    try:
        emails = await api_gen_random_mailbox(1)
        email = emails[0]
    except Exception as e:
        logger.error(f"API genRandomMailbox failed: {e}")
        await update.message.reply_text("⚠️ Could not generate email right now. Try again later.")
        return

    now = datetime.now(timezone.utc).isoformat()
    try:
        await db_execute(
            "INSERT INTO generated_emails (email_address, user_id, created_at) VALUES (?, ?, ?)",
            (email, user.id, now),
        )
    except sqlite3.IntegrityError:
        await update.message.reply_text("⚠️ That email already exists. Try again.")
        return

    await update.message.reply_text(f"✅ New temp email created:\n`{email}`", parse_mode="Markdown")

async def list_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's temporary emails."""
    user = update.effective_user
    rows = await db_fetchall(
        "SELECT email_address, created_at FROM generated_emails WHERE user_id=? ORDER BY created_at",
        (user.id,),
    )
    if not rows:
        await update.message.reply_text("📭 You have no active temp emails. Use /create.")
        return

    lines = []
    for i, row in enumerate(rows, 1):
        lines.append(f"{i}. `{row['email_address']}` (created {row['created_at'][:10]})")
    await update.message.reply_text(
        "📋 Your temp emails:\n" + "\n".join(lines),
        parse_mode="Markdown",
    )

async def delete_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a temp email by its list index."""
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Usage: /delete <index>\nExample: /delete 1")
        return

    try:
        index = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Index must be a number.")
        return

    rows = await db_fetchall(
        "SELECT email_address FROM generated_emails WHERE user_id=? ORDER BY created_at",
        (user.id,),
    )
    if index < 1 or index > len(rows):
        await update.message.reply_text("❌ Invalid index.")
        return

    email = rows[index - 1]["email_address"]
    await db_execute("DELETE FROM generated_emails WHERE email_address=?", (email,))
    await update.message.reply_text(f"🗑️ Temp email `{email}` deleted.", parse_mode="Markdown")

async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual inbox check for one email."""
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Usage: /inbox <index>\nExample: /inbox 1")
        return

    try:
        index = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Index must be a number.")
        return

    rows = await db_fetchall(
        "SELECT email_address FROM generated_emails WHERE user_id=? ORDER BY created_at",
        (user.id,),
    )
    if index < 1 or index > len(rows):
        await update.message.reply_text("❌ Invalid index.")
        return

    email = rows[index - 1]["email_address"]
    login, domain = email.split("@")
    try:
        messages = await api_get_messages(login, domain)
    except Exception as e:
        logger.error(f"Failed to fetch messages for {email}: {e}")
        await update.message.reply_text("⚠️ Could not check inbox. Try again later.")
        return

    if not messages:
        await update.message.reply_text("📭 Inbox is empty.")
        return

    for msg in messages:
        text = (
            f"📬 *New message in {email}*\n"
            f"From: {msg['from']}\n"
            f"Subject: {msg['subject']}\n"
            f"Date: {msg['date']}\n"
            f"ID: `{msg['id']}`\n\n"
            f"Use /read {index} {msg['id']} for full content."
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    # Update last_notified_id to the maximum id seen so auto‑check won't repeat them
    if messages:
        max_id = max(int(m["id"]) for m in messages)
        await db_execute(
            "UPDATE generated_emails SET last_notified_id=? WHERE email_address=?",
            (max_id, email),
        )

async def read_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Read full content of a message."""
    user = update.effective_user
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /read <email_index> <message_id>")
        return

    try:
        index = int(context.args[0])
        msg_id = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Both arguments must be numbers.")
        return

    rows = await db_fetchall(
        "SELECT email_address FROM generated_emails WHERE user_id=? ORDER BY created_at",
        (user.id,),
    )
    if index < 1 or index > len(rows):
        await update.message.reply_text("❌ Invalid email index.")
        return

    email = rows[index - 1]["email_address"]
    login, domain = email.split("@")
    try:
        full = await api_read_message(login, domain, msg_id)
    except Exception as e:
        logger.error(f"Failed to read message {msg_id} from {email}: {e}")
        await update.message.reply_text("⚠️ Could not fetch the message.")
        return

    # Prefer plain text, fallback to HTML body
    body = full.get("textBody") or full.get("body") or "(no content)"
    # Truncate to avoid Telegram message limit
    if len(body) > 4000:
        body = body[:4000] + "\n... (truncated)"

    text = (
        f"📧 *Message {msg_id}*\n"
        f"From: {full['from']}\n"
        f"Subject: {full['subject']}\n"
        f"Date: {full['date']}\n\n"
        f"{body}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ---------- Admin commands ----------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message to all users (admin only)."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin only.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    users = await db_fetchall("SELECT user_id FROM users")
    sent = 0
    for row in users:
        uid = row["user_id"]
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 Broadcast:\n\n{message}")
            sent += 1
        except Exception as e:
            logger.warning(f"Failed to send broadcast to {uid}: {e}")

    await update.message.reply_text(f"✅ Broadcast sent to {sent}/{len(users)} users.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics (admin only)."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin only.")
        return

    total_users = await db_fetchone("SELECT COUNT(*) as cnt FROM users")
    total_emails = await db_fetchone("SELECT COUNT(*) as cnt FROM generated_emails")
    await update.message.reply_text(
        f"📊 Stats:\n"
        f"👥 Total users: {total_users['cnt']}\n"
        f"📧 Active temp emails: {total_emails['cnt']}"
    )

# ---------- Auto inbox check (runs every 15 seconds) ----------
async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    """Check all active temp emails and notify users of new messages."""
    rows = await db_fetchall("SELECT email_address, user_id, last_notified_id FROM generated_emails")
    if not rows:
        return

    for row in rows:
        email = row["email_address"]
        user_id = row["user_id"]
        last_id = row["last_notified_id"]
        login, domain = email.split("@")

        try:
            messages = await api_get_messages(login, domain)
        except Exception as e:
            logger.error(f"Auto‑check failed for {email}: {e}")
            continue

        if not messages:
            continue

        new_msgs = [m for m in messages if int(m["id"]) > last_id]
        if not new_msgs:
            continue

        max_id = max(int(m["id"]) for m in new_msgs)
        for msg in new_msgs:
            text = (
                f"📬 *New mail in {email}*\n"
                f"From: {msg['from']}\n"
                f"Subject: {msg['subject']}\n"
                f"Date: {msg['date']}\n"
                f"ID: `{msg['id']}`"
            )
            try:
                await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Failed to notify {user_id} about {email}: {e}")

        await db_execute(
            "UPDATE generated_emails SET last_notified_id=? WHERE email_address=?",
            (max_id, email),
        )

# ---------- Main application ----------
async def main():
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create))
    application.add_handler(CommandHandler("list", list_emails))
    application.add_handler(CommandHandler("delete", delete_email))
    application.add_handler(CommandHandler("inbox", inbox))
    application.add_handler(CommandHandler("read", read_message))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("stats", stats))

    # Auto check job every 15 seconds
    job_queue = application.job_queue
    job_queue.run_repeating(auto_check, interval=15, first=5)

    logger.info("Bot started. Polling...")
    await application.run_polling()

if __name__ == "__main__":
    init_db()              # synchronous init before the event loop starts
    asyncio.run(main())    # clean event loop management, works on Render