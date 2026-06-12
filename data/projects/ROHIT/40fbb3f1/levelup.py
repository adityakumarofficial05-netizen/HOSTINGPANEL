import logging
import asyncio
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import aiohttp

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== CONFIGURATION ====================
TOKEN = "8343949122:AAEj_6MeaCAFFgemzp3nEKzOkuQhNJMbpRk"  # BotFather se mila hua token yahan daalein
ADMIN_ID = 7607314151              # Apni real Telegram User ID yahan daalein

# Game API Endpoints (Apni captured APIs se replace karein)
LOGIN_URL = "https://api.game.com/v1/login"
LEVELUP_URL = "https://api.game.com/v1/claim_xp"
# =======================================================

# Local Database Setup (Stats track karne ke liye)
DB_FILE = "bot_stats.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"total_users": [], "success_claims": 0, "active_loops": 0}, f)

def get_stats():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def update_stats(key, value, is_list=False):
    data = get_stats()
    if is_list:
        if value not in data[key]:
            data[key].append(value)
    else:
        data[key] += value
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# --- USER SIDE COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    update_stats("total_users", user_id, is_list=True)
    
    # Check if Admin
    if user_id == ADMIN_ID:
        await send_admin_dashboard(update.message.reply_text)
        return

    await update.message.reply_text(
        "👋 **Welcome to Level-Up Automation Bot!**\n\n"
        "Aap niche diye gaye command se apni ID level-up kar sakte hain:\n"
        "👉 Format: `/levelup [UID] [PASSWORD]`",
        parse_mode="Markdown"
    )

async def level_up_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        uid = context.args[0]
        password = context.args[1]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ **Format Galat Hai!**\nUse karein: `/levelup UID PASSWORD`", parse_mode="Markdown")
        return

    status_message = await update.message.reply_text("⏳ **Game server se connect ho raha hai...**", parse_mode="Markdown")
    update_stats("active_loops", 1)

    async with aiohttp.ClientSession() as session:
        # 1. Login Request
        login_payload = {"uid": uid, "password": password, "device": "android"}
        try:
            async with session.post(LOGIN_URL, json=login_payload, timeout=10) as response:
                if response.status != 200:
                    await status_message.edit_text("❌ **Login Failed!** UID ya Password galat hai.")
                    update_stats("active_loops", -1)
                    return
                
                res_data = await response.json()
                access_token = res_data.get("token")
        except Exception as e:
            await status_message.edit_text(f"❌ **Server Error:** Connection timeout!")
            update_stats("active_loops", -1)
            return

        await status_message.edit_text("✅ **Login Successful!** Automation loop shuru ho raha hai...")

        # 2. Automation Loop (5 Tasks/Matches Example)
        headers = {"Authorization": f"Bearer {access_token}"}
        success_count = 0
        
        for i in range(1, 6):
            try:
                async with session.post(LEVELUP_URL, headers=headers, timeout=10) as action_res:
                    if action_res.status == 200:
                        success_count += 1
                        update_stats("success_claims", 1)
                        await status_message.edit_text(f"🚀 **Processing:** [{success_count}/5] XP claimed successfully!")
            except:
                pass
            await asyncio.sleep(3) # Anti-ban safety delay

        await status_message.edit_text(f"🎉 **Automation Complete!**\n\n🆔 UID: `{uid}`\n✅ Successfully claimed {success_count} levels/XP!", parse_mode="Markdown")
        update_stats("active_loops", -1)

# --- ADMIN SIDE COMPONENTS ---
async def send_admin_dashboard(reply_func):
    stats = get_stats()
    text = (
        "⚙️ **MASTER CORE - ADMIN PANEL** ⚙️\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 Bot Status: 🟢 ONLINE\n"
        f"👥 Total Users: {len(stats['total_users'])}\n"
        f"🔄 Active Loops: {stats['active_loops']}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Neeche diye gaye buttons se control karein:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📊 View Stats", callback_data="admin_stats"),
            InlineKeyboardButton("🔄 Active Loops", callback_data="admin_loops")
        ],
        [
            InlineKeyboardButton("🚫 Ban/Unban User", callback_data="admin_ban"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("📜 Close Panel", callback_data="admin_close")
        ]
    ]
    await reply_func(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Access Denied! Sirf Admin ke liye hai.", show_alert=True)
        return

    data = query.data
    stats = get_stats()

    if data == "admin_main":
        keyboard = [
            [InlineKeyboardButton("📊 View Stats", callback_data="admin_stats"), InlineKeyboardButton("🔄 Active Loops", callback_data="admin_loops")],
            [InlineKeyboardButton("🚫 Ban/Unban User", callback_data="admin_ban"), InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📜 Close Panel", callback_data="admin_close")]
        ]
        await query.edit_message_text(
            f"⚙️ **MASTER CORE - ADMIN PANEL** ⚙️\n━━━━━━━━━━━━━━━━━━━━━\n🤖 Bot Status: 🟢 ONLINE\n👥 Users: {len(stats['total_users'])}\n━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif data == "admin_stats":
        text = f"📊 **Live Database Stats:**\n\n📌 Total Registered Users: {len(stats['total_users'])}\n📌 Total Success Level-ups: {stats['success_claims']}"
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="admin_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "admin_loops":
        text = f"🔄 **Active Automation Loops:**\n\nAbhi total `{stats['active_loops']}` IDs background me level-up ho rahi hain."
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="admin_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "admin_ban":
        text = "🚫 **User Management:**\n\nKisi user ko block/ban karne ke liye use karein:\n`/ban [UserID]`"
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="admin_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "admin_broadcast":
        text = "📢 **Global Broadcast:**\n\nSaare users ko message bhejne ke liye typing form use karein:\n`/broadcast [Aapka Message]`"
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="admin_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data == "admin_close":
        await query.edit_message_text("🔒 Admin panel closed successfully.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("levelup", level_up_process))
    
    # Callback Query Handler (Buttons click ke liye)
    app.add_handler(CallbackQueryHandler(button_click_handler))
    
    print("🚀 Merged Bot running successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
