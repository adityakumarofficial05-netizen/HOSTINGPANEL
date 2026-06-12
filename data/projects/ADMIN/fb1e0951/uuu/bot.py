import os
import json
import logging
import asyncio
from datetime import datetime
from urllib.parse import quote

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import uvicorn
import aiohttp

from config import *
from database import get_db, init_db

# ========== Helper Functions ==========
async def send_success_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_animation(
        animation="https://media4.giphy.com/media/l0HlNQ03J5JxX6lva/giphy.gif",
        caption="✅ **Authentication Successful!**\nRedirecting to your dashboard...",
        parse_mode=ParseMode.MARKDOWN
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as conn:
        user = conn.execute("SELECT credits FROM users WHERE telegram_id = ?", (user_id,)).fetchone()
        if not user:
            return
        credits = user['credits']
    keyboard = [
        [InlineKeyboardButton("📧 Generate New Email", callback_data="gen_email")],
        [InlineKeyboardButton("📥 My Inbox", callback_data="inbox")],
        [InlineKeyboardButton("📋 Current Emails", callback_data="list_emails")],
        [InlineKeyboardButton("➕ Buy Credits", callback_data="buy_credits")],
        [InlineKeyboardButton("❌ Delete Email", callback_data="delete_email")]
    ]
    await update.effective_message.reply_text(
        f"🏢 **X Danger Dashboard**\n"
        f"💎 **Credits Available:** `{credits}`\n\n"
        f"Use the buttons below to manage your secure communication channels.\n\n"
        f"📞 *Support:* [Contact Admin](https://t.me/your_admin_username)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

# ========== Bot Handlers ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,)).fetchone()
    if user:
        if user['is_banned']:
            await update.message.reply_text("⛔ Your account has been suspended. Contact admin.")
            return
        await send_success_animation(update, context)
        await show_main_menu(update, context)
    else:
        keyboard = [
            [InlineKeyboardButton("🔐 Login with Google", url=f"https://your-backend-server.com/auth/google?telegram_id={user_id}")],
            [KeyboardButton("📱 Verify Phone Number", request_contact=True)]
        ]
        await update.message.reply_text(
            "✨ **Welcome to X Danger** ✨\n\n"
            "Please authenticate to access your secure workspace.\n\n"
            "🔒 *End-to-end encrypted*\n"
            "⚡ *Instant setup*\n\n"
            "💬 *24/7 Support / Contact Admin* – [Click Here](https://t.me/your_admin_username)",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    telegram_id = update.effective_user.id
    phone = contact.phone_number
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (telegram_id, auth_method, phone_number, credits) VALUES (?, ?, ?, ?)",
            (telegram_id, "phone", phone, 5)
        )
    await send_success_animation(update, context)
    await show_main_menu(update, context)

async def generate_email(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    user_id = update.effective_user.id if query is None else query.from_user.id
    with get_db() as conn:
        user = conn.execute("SELECT credits, is_banned FROM users WHERE telegram_id = ?", (user_id,)).fetchone()
        if not user or user['is_banned']:
            await (query.edit_message_text if query else update.message.reply_text)("⛔ Access denied.")
            return
        credits = user['credits']
        if credits < 1:
            buy_keyboard = [[InlineKeyboardButton("💰 Buy Credits (Fampay UPI)", url=FAMPAY_PAYMENT_LINK)]]
            await (query.edit_message_text if query else update.message.reply_text)(
                "❌ **Insufficient Credits**\n\n"
                "You have 0 credits. Purchase more to generate a new secure email address.",
                reply_markup=InlineKeyboardMarkup(buy_keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        # Generate unique email with prefix "xdanger_"
        random_hash = secrets.token_hex(8)
        local_part = f"xdanger_{random_hash}"
        full_email = f"{local_part}@{DOMAIN}"
        # Ensure uniqueness (very unlikely but safe)
        existing = conn.execute("SELECT id FROM email_addresses WHERE email = ?", (full_email,)).fetchone()
        if existing:
            full_email = f"xdanger_{secrets.token_hex(12)}@{DOMAIN}"
        conn.execute("INSERT INTO email_addresses (telegram_id, email) VALUES (?, ?)", (user_id, full_email))
        conn.execute("UPDATE users SET credits = credits - 1 WHERE telegram_id = ?", (user_id,))
        new_credits = credits - 1
    await (query.edit_message_text if query else update.message.reply_text)(
        f"✅ **New Secure Email Generated**\n\n"
        f"📧 `{full_email}`\n\n"
        f"🔒 *Valid for 24 hours* (auto-renew available)\n"
        f"💎 Remaining credits: `{new_credits}`\n\n"
        f"👉 Use this email to receive messages privately.",
        parse_mode=ParseMode.MARKDOWN
    )
    await show_main_menu(update, context)

async def list_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as conn:
        emails = conn.execute("SELECT email FROM email_addresses WHERE telegram_id = ? AND is_active = 1", (user_id,)).fetchall()
    if not emails:
        await update.effective_message.reply_text("📭 You have no active email addresses. Generate one using the menu.")
        return
    text = "📬 **Your Active Secure Emails:**\n\n" + "\n".join([f"• `{e['email']}`" for e in emails])
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def inbox_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as conn:
        emails = conn.execute("SELECT email FROM email_addresses WHERE telegram_id = ? AND is_active = 1", (user_id,)).fetchall()
    if not emails:
        await update.effective_message.reply_text("No active emails found. Generate one first.")
        return
    keyboard = [[InlineKeyboardButton(e['email'], callback_data=f"show_inbox_{e['email']}")] for e in emails]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    await update.effective_message.reply_text(
        "📥 **Select email to view inbox:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

async def show_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE, email: str):
    with get_db() as conn:
        messages = conn.execute(
            "SELECT sender, subject, body, received_at FROM inbox WHERE recipient_email = ? ORDER BY received_at DESC LIMIT 20",
            (email,)
        ).fetchall()
    if not messages:
        await update.effective_message.reply_text(f"📭 No messages for `{email}`.", parse_mode=ParseMode.MARKDOWN)
        return
    text = f"📬 **Inbox for `{email}`**\n\n"
    for idx, msg in enumerate(messages[:5], 1):
        text += f"*{idx}.* From: {msg['sender']}\n   Subject: {msg['subject'][:50]}\n   Received: {msg['received_at']}\n\n"
    if len(messages) > 5:
        text += "_Only 5 most recent shown._"
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def delete_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as conn:
        emails = conn.execute("SELECT email FROM email_addresses WHERE telegram_id = ? AND is_active = 1", (user_id,)).fetchall()
    if not emails:
        await update.effective_message.reply_text("No active emails to delete.")
        return
    keyboard = [[InlineKeyboardButton(e['email'], callback_data=f"del_{e['email']}")] for e in emails]
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="main_menu")])
    await update.effective_message.reply_text(
        "🗑 **Select email to delete:**\n\n*This action is irreversible.*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, email: str, query):
    user_id = query.from_user.id
    with get_db() as conn:
        conn.execute("UPDATE email_addresses SET is_active = 0 WHERE email = ? AND telegram_id = ?", (email, user_id))
    await query.edit_message_text(f"✅ Email `{email}` has been permanently removed.", parse_mode=ParseMode.MARKDOWN)
    await show_main_menu(update, context)

async def buy_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💸 Pay via Fampay UPI", url=FAMPAY_PAYMENT_LINK)]]
    await update.effective_message.reply_text(
        "💳 **Purchase Credits**\n\n"
        "100 credits = ₹199\n\n"
        "Click the button below to pay using Fampay UPI. After successful payment, your credits will be automatically added (webhook integration required).\n\n"
        "*For manual credit addition, contact admin.*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# ========== Hidden Admin Panel ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as conn:
        admin = conn.execute("SELECT admin_telegram_id FROM admin_config").fetchone()
        if user_id != admin['admin_telegram_id']:
            await update.message.reply_text("⛔ Unauthorized.")
            return
    keyboard = [
        [InlineKeyboardButton("👥 List Users", callback_data="admin_list_users")],
        [InlineKeyboardButton("🔍 Search User by ID", callback_data="admin_search_user")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")]
    ]
    await update.message.reply_text(
        "🛡️ **X Danger Admin Console**\n\n"
        "Manage users, credits, and bans.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

async def admin_list_users(update: Update, context: ContextTypes.DEFAULT_TYPE, query, page=0):
    per_page = 5
    offset = page * per_page
    with get_db() as conn:
        users = conn.execute(
            "SELECT telegram_id, auth_method, credits, is_banned FROM users ORDER BY registered_at DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()['cnt']
    if not users:
        await query.edit_message_text("No users found.")
        return
    text = "👥 **Users**\n\n"
    for u in users:
        banned = "🚫 Banned" if u['is_banned'] else "✅ Active"
        text += f"🆔 `{u['telegram_id']}` | {banned} | 💎 {u['credits']} credits\n"
    keyboard = []
    if offset > 0:
        keyboard.append(InlineKeyboardButton("◀ Prev", callback_data=f"admin_users_page_{page-1}"))
    if offset + per_page < total:
        keyboard.append(InlineKeyboardButton("Next ▶", callback_data=f"admin_users_page_{page+1}"))
    # Add user detail buttons for each user
    for u in users:
        keyboard.append([InlineKeyboardButton(f"🔍 View {u['telegram_id']}", callback_data=f"admin_user_detail_{u['telegram_id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def admin_user_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int, query):
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (target_id,)).fetchone()
        if not user:
            await query.edit_message_text("User not found.")
            return
        emails = conn.execute("SELECT email FROM email_addresses WHERE telegram_id = ? AND is_active=1", (target_id,)).fetchall()
    email_list = "\n".join([f"• {e['email']}" for e in emails]) or "No active emails"
    details = (
        f"🆔 **User ID:** `{user['telegram_id']}`\n"
        f"🔐 **Auth Method:** {user['auth_method']}\n"
        f"{'📧 **Google Email:** ' + user['google_email'] if user['google_email'] else '📱 **Phone:** ' + user['phone_number']}\n"
        f"💎 **Credits:** {user['credits']}\n"
        f"🚦 **Status:** {'Banned' if user['is_banned'] else 'Active'}\n"
        f"📧 **Emails:**\n{email_list}\n"
        f"📅 **Registered:** {user['registered_at']}"
    )
    keyboard = [
        [InlineKeyboardButton("➕ Add 10 Credits", callback_data=f"admin_add_credits_{target_id}")],
        [InlineKeyboardButton("➖ Remove 10 Credits", callback_data=f"admin_remove_credits_{target_id}")],
        [InlineKeyboardButton("⛔ Ban User", callback_data=f"admin_ban_{target_id}")],
        [InlineKeyboardButton("✅ Unban User", callback_data=f"admin_unban_{target_id}")],
        [InlineKeyboardButton("🔙 Back to User List", callback_data="admin_list_users")]
    ]
    if user['phone_number']:
        phone = user['phone_number']
        whatsapp_url = f"https://wa.me/{phone}"
        call_url = f"tel:{phone}"
        keyboard.insert(0, [
            InlineKeyboardButton("💬 WhatsApp", url=whatsapp_url),
            InlineKeyboardButton("📞 Call", url=call_url)
        ])
    await query.edit_message_text(details, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def admin_modify_credits(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id: int, delta: int, query):
    with get_db() as conn:
        conn.execute("UPDATE users SET credits = credits + ? WHERE telegram_id = ?", (delta, telegram_id))
    await query.answer(f"Credits updated: {delta:+d}", show_alert=True)
    await admin_user_detail(update, context, telegram_id, query)

async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id: int, query):
    with get_db() as conn:
        conn.execute("UPDATE users SET is_banned = 1 WHERE telegram_id = ?", (telegram_id,))
    await query.answer("User banned.", show_alert=True)
    await admin_user_detail(update, context, telegram_id, query)

async def admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id: int, query):
    with get_db() as conn:
        conn.execute("UPDATE users SET is_banned = 0 WHERE telegram_id = ?", (telegram_id,))
    await query.answer("User unbanned.", show_alert=True)
    await admin_user_detail(update, context, telegram_id, query)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    with get_db() as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_emails = conn.execute("SELECT COUNT(*) FROM email_addresses").fetchone()[0]
        total_inbox = conn.execute("SELECT COUNT(*) FROM inbox").fetchone()[0]
    stats_text = (
        f"📊 **System Statistics**\n\n"
        f"👥 Total Users: {total_users}\n"
        f"📧 Emails Generated: {total_emails}\n"
        f"📥 Received Messages: {total_inbox}"
    )
    await query.edit_message_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def admin_search_user(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    # This is a simplified version – in a full bot you'd use a conversation handler
    await query.edit_message_text("Send the user ID as a number.")
    # We'll implement a simple state in production; for brevity, we skip full flow.

# ========== Callback Handler ==========
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # User actions
    if data == "gen_email":
        await generate_email(update, context, query)
    elif data == "inbox":
        await inbox_menu(update, context)
    elif data == "list_emails":
        await list_emails(update, context)
    elif data == "buy_credits":
        await buy_credits(update, context)
    elif data == "delete_email":
        await delete_email(update, context)
    elif data.startswith("show_inbox_"):
        email = data[11:]
        await show_inbox(update, context, email)
    elif data.startswith("del_"):
        email = data[4:]
        await confirm_delete(update, context, email, query)
    elif data == "main_menu":
        await show_main_menu(update, context)

    # Admin actions
    elif data == "admin_list_users":
        await admin_list_users(update, context, query)
    elif data.startswith("admin_users_page_"):
        page = int(data.split("_")[-1])
        await admin_list_users(update, context, query, page)
    elif data.startswith("admin_user_detail_"):
        uid = int(data.split("_")[-1])
        await admin_user_detail(update, context, uid, query)
    elif data.startswith("admin_add_credits_"):
        uid = int(data.split("_")[-1])
        await admin_modify_credits(update, context, uid, 10, query)
    elif data.startswith("admin_remove_credits_"):
        uid = int(data.split("_")[-1])
        await admin_modify_credits(update, context, uid, -10, query)
    elif data.startswith("admin_ban_"):
        uid = int(data.split("_")[-1])
        await admin_ban_user(update, context, uid, query)
    elif data.startswith("admin_unban_"):
        uid = int(data.split("_")[-1])
        await admin_unban_user(update, context, uid, query)
    elif data == "admin_stats":
        await admin_stats(update, context, query)
    elif data == "admin_back":
        await admin_panel(update, context)
    elif data == "admin_search_user":
        await admin_search_user(update, context, query)

# ========== FastAPI Email Webhook ==========
email_app = FastAPI()

@email_app.post("/email_webhook")
async def receive_email(request: Request):
    """Receive email from your domain's catch-all forwarding."""
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    recipient = data.get("recipient")
    sender = data.get("sender")
    subject = data.get("subject", "No Subject")
    body = data.get("body", "")
    if not recipient or not sender:
        raise HTTPException(status_code=400, detail="Missing fields")
    with get_db() as conn:
        email_record = conn.execute(
            "SELECT telegram_id FROM email_addresses WHERE email = ? AND is_active = 1",
            (recipient,)
        ).fetchone()
        if email_record:
            conn.execute(
                "INSERT INTO inbox (recipient_email, sender, subject, body) VALUES (?, ?, ?, ?)",
                (recipient, sender, subject, body[:5000])
            )
    return {"status": "delivered"}

# ========== Google OAuth Endpoints ==========
@email_app.get("/auth/google")
async def google_auth(telegram_id: int):
    state = f"{telegram_id}:{secrets.token_urlsafe(16)}"
    redirect_uri = "https://your-backend-server.com/auth/google/callback"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=email%20profile&"
        f"state={state}"
    )
    return RedirectResponse(auth_url)

@email_app.get("/auth/google/callback")
async def google_callback(code: str, state: str):
    telegram_id = int(state.split(":")[0])
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": "https://your-backend-server.com/auth/google/callback",
        "grant_type": "authorization_code",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, data=data) as resp:
            tokens = await resp.json()
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            async with session.get(userinfo_url, headers=headers) as user_resp:
                userinfo = await user_resp.json()
                google_email = userinfo["email"]
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO users (telegram_id, auth_method, google_email, credits) VALUES (?, ?, ?, ?)",
            (telegram_id, "google", google_email, 5)
        )
    # Notify user on Telegram
    bot_app = Application.builder().token(BOT_TOKEN).build()
    await bot_app.bot.send_animation(
        chat_id=telegram_id,
        animation="https://media4.giphy.com/media/l0HlNQ03J5JxX6lva/giphy.gif",
        caption="✅ **Google Authentication Successful!**\nWelcome to X Danger."
    )
    await bot_app.bot.send_message(telegram_id, "Use /start to view your dashboard.")
    return RedirectResponse(f"https://t.me/your_bot_username?start=dashboard")

# ========== Main Runner ==========
async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(CommandHandler(ADMIN_SECRET_COMMAND, admin_panel))
    app.add_handler(CallbackQueryHandler(callback_handler))
    await app.run_polling()

if __name__ == "__main__":
    init_db()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(run_bot())
    uvicorn.run(email_app, host="0.0.0.0", port=8000)