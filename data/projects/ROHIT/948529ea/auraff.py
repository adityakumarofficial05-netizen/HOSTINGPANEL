"""
================================================================================
💎 PRODUCTION-GRADE MASTER CORE SHOP ENGINE v8.1 (FIXED & EMORIZED) 💎
================================================================================
Framework: python-telegram-bot v20.x (Async/Await)
Environment: Termux / Linux Cloud VPS (Python 3.13+ Optimized)
================================================================================
"""

import os
import sys
import logging
import asyncio
import time
import datetime
import json
import aiohttp
from typing import Dict, Any, Union, List

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Bot
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters, 
    ContextTypes
)

# ==========================================
# 🛑 CORE CONFIGURATION INTERFACES
# ==========================================
BOT_TOKEN: str = "8108100182:AAGm_41rsUinN1UQEfV1psXpcpCWdaiwhy8"
ADMIN_ID: int = 7607314151  # Apna Telegram Numeric ID yahan dalein
QR_IMAGE_URL: str = "https://t.me/MickeyXPayy/17"
SUPPORT_HANDLE: str = "DEVILxBHAI"  
FEEDBACK_LINK: str = "https://t.me/MickeyFeedback"

# FamPay Live Engine Configurations
MERCHANT_UPI_ID: str = "samiran7@fam"
FAMPAY_API_KEY: str = "FAM_88856c9f952b66f34313e687282a5e79c669841d24873eef"
API_BASE_URL: str = "https://fampay.anujbots.xyz"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

LOCAL_DB_FILE = "local_db.json"

# ==========================================
# 💾 DATABASE STORAGE ENGINES (JSON NODE)
# ==========================================
def load_local_db() -> Dict[str, Any]:
    if not os.path.exists(LOCAL_DB_FILE):
        default_structure = {
            "users": {}, 
            "categories": {
                "ff_non_root": {"name": "🔥 FF Apk Mod Non Root", "products": {}},
                "ff_root": {"name": "🚀 FF Root", "products": {}},
                "ff_lvl8": {"name": "🎖️ 8 Lvl Id", "products": {}}
            },
            "transactions": {},
            "stats": {"total_sold_keys": 0, "total_revenue": 0.0}
        }
        with open(LOCAL_DB_FILE, 'w') as f:
            json.dump(default_structure, f, indent=4)
        return default_structure
    try:
        with open(LOCAL_DB_FILE, 'r') as f:
            data = json.load(f)
            if "stats" not in data:
                data["stats"] = {"total_sold_keys": 0, "total_revenue": 0.0}
            return data
    except Exception:
        return {"users": {}, "categories": {}, "transactions": {}, "stats": {"total_sold_keys": 0, "total_revenue": 0.0}}

def save_local_db(data: Dict[str, Any]):
    with open(LOCAL_DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

class SmartDatabaseRouter:
    @staticmethod
    def get_node(path: str) -> Any:
        ldb = load_local_db()
        parts = path.strip('/').split('/')
        current = ldb
        for part in parts:
            if not part: continue
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def set_node(path: str, value: Any):
        ldb = load_local_db()
        parts = path.strip('/').split('/')
        current = ldb
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
        save_local_db(ldb)

    @staticmethod
    def delete_node(path: str):
        ldb = load_local_db()
        parts = path.strip('/').split('/')
        current = ldb
        for part in parts[:-1]:
            if part in current:
                current = current[part]
            else:
                return
        if parts[-1] in current:
            del current[parts[-1]]
        save_local_db(ldb)

def initialize_user_registers(user_id: Union[int, str], username: str = "User", first_name: str = "") -> Dict[str, Any]:
    user_id = str(user_id)
    profile_data = SmartDatabaseRouter.get_node(f'users/{user_id}')
    if not profile_data:
        profile_data = {
            'balance': 0.0,
            'username': username,
            'first_name': first_name,
            'registered_at': str(datetime.datetime.now()),
            'purchased_keys': []
        }
        SmartDatabaseRouter.set_node(f'users/{user_id}', profile_data)
    else:
        if 'purchased_keys' not in profile_data:
            SmartDatabaseRouter.set_node(f'users/{user_id}/purchased_keys', [])
    return profile_data

def process_wallet_balance_mutation(user_id: Union[int, str], amount: float) -> float:
    user_id = str(user_id)
    current_snapshot = SmartDatabaseRouter.get_node(f'users/{user_id}') or {}
    old_balance = float(current_snapshot.get('balance', 0.0))
    new_balance = max(0.0, old_balance + amount)
    SmartDatabaseRouter.set_node(f'users/{user_id}/balance', new_balance)
    return new_balance

def get_day_emoji(day_str: str) -> str:
    """Days count ke hisab se active matching premium emojis allocate karne ka logic"""
    try:
        days = int(day_str)
        if days <= 1: return "⚡"
        elif days <= 3: return "🔥"
        elif days <= 7: return "🚀"
        elif days <= 30: return "👑"
        else: return "⏳"
    except ValueError:
        return "📋"

# ==========================================
# 🎛️ UI KEYBOARD INTERFACES
# ==========================================
def render_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ Shop", callback_data="ui_shop_cats")],
        [InlineKeyboardButton("👤 Profile", callback_data="ui_profile"), InlineKeyboardButton("📖 How To Use", callback_data="ui_how_to_use")],
        [InlineKeyboardButton("⚡ Add Fund (Auto)", callback_data="ui_route_auto"), InlineKeyboardButton("🔑 My Keys", callback_data="ui_my_keys")],
        [InlineKeyboardButton("📈 Review And Proof", url=FEEDBACK_LINK)],
        [InlineKeyboardButton("💼 Manual Deposit", callback_data="ui_route_manual")],
        [InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{SUPPORT_HANDLE}")]
    ])

def render_matrix_dialpad(mode: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1", callback_data=f"pad_{mode}_1"), InlineKeyboardButton("2", callback_data=f"pad_{mode}_2"), InlineKeyboardButton("3", callback_data=f"pad_{mode}_3")],
        [InlineKeyboardButton("4", callback_data=f"pad_{mode}_4"), InlineKeyboardButton("5", callback_data=f"pad_{mode}_5"), InlineKeyboardButton("6", callback_data=f"pad_{mode}_6")],
        [InlineKeyboardButton("7", callback_data=f"pad_{mode}_7"), InlineKeyboardButton("8", callback_data=f"pad_{mode}_8"), InlineKeyboardButton("9", callback_data=f"pad_{mode}_9")],
        [InlineKeyboardButton("10", callback_data=f"pad_{mode}_10")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"pad_{mode}_backspace"), InlineKeyboardButton("✅ Confirm", callback_data=f"pad_{mode}_commit")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
    ])

def render_admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗂️ Manage Category", callback_data="adm_manage_cats")],
        [InlineKeyboardButton("📊 View Bot Stats", callback_data="adm_view_stats"), InlineKeyboardButton("📢 Broadcast Dynamic Media", callback_data="adm_trigger_bc")],
        [InlineKeyboardButton("💰 Manage Wallet", callback_data="adm_manage_bal_menu")],
        [InlineKeyboardButton("❌ Close Panel", callback_data="adm_close_panel")]
    ])

def render_admin_category_management_markup(cid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Products Name & List", callback_data=f"adm_list_prods_{cid}")],
        [InlineKeyboardButton("➕ Add Product", callback_data=f"adm_seq_addprod_{cid}"), InlineKeyboardButton("➖ Remove Product", callback_data=f"adm_seq_remprod_{cid}")],
        [InlineKeyboardButton("➕ Add Days", callback_data=f"adm_seq_adddays_{cid}"), InlineKeyboardButton("➖ Remove Days", callback_data=f"adm_seq_remdays_{cid}")],
        [InlineKeyboardButton("🔑 Add Key", callback_data=f"adm_seq_addkey_{cid}"), InlineKeyboardButton("🗑️ Remove Key", callback_data=f"adm_seq_remkey_{cid}")],
        [InlineKeyboardButton("🔍 Check Keys Stock", callback_data=f"adm_check_keys_{cid}")],
        [InlineKeyboardButton("🔙 Back to Management List", callback_data="adm_manage_cats")]
    ])

def render_admin_balance_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Check User Balance", callback_data="adm_bal_check")],
        [InlineKeyboardButton("➕ Add Balance (Credit)", callback_data="adm_bal_add")],
        [InlineKeyboardButton("➖ Remove Balance (Debit)", callback_data="adm_bal_remove")],
        [InlineKeyboardButton("🔙 Back to Admin Dashboard", callback_data="back_to_admin")]
    ])

def render_back_navigation_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back To Main Menu", callback_data="back_main")]])

def render_admin_back_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin", callback_data="back_to_admin")]])

# ==========================================
# 🧭 CORE TELEGRAM TELEMETRY HANDLERS
# ==========================================
async def start_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user = update.effective_user
    username = user.username if user.username else user.first_name
    initialize_user_registers(user.id, username, user.first_name)
    await build_and_transmit_main_frame(context.bot, update.message.chat_id, user.id, username)

async def admin_panel_launcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("⚡ **MASTER ADMINISTRATIVE INTERFACE PANEL** ⚡", reply_markup=render_admin_panel_keyboard())

async def build_and_transmit_main_frame(bot: Bot, chat_id: int, user_id: int, username: str, edit_msg_id: int = None):
    user_record = initialize_user_registers(user_id, username)
    dashboard_text = (
        f"🤖 **💎 MICKEY MAIN DASHBOARD CORE 💎**\n\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"💰 **Available Balance:** ₹{user_record['balance']:.2f}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ High-Speed Automated Matrix Framework\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 **Select your desired operation from options node beneath:**"
    )
    if edit_msg_id:
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=edit_msg_id, text=dashboard_text, parse_mode="Markdown", reply_markup=render_main_menu_keyboard())
            return
        except Exception: pass
    await bot.send_message(chat_id=chat_id, text=dashboard_text, parse_mode="Markdown", reply_markup=render_main_menu_keyboard())

# ==========================================
# 🎚️ CALLBACK ROUTING INTERFACE ENGINE
# ==========================================
async def global_callback_routing_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username if query.from_user.username else query.from_user.first_name
    chat_id = query.message.chat_id
    data = query.data

    if data == "back_main":
        try: await query.message.delete()
        except Exception: pass
        await build_and_transmit_main_frame(context.bot, chat_id, user_id, username)
        return

    elif data == "ui_profile":
        user_record = initialize_user_registers(user_id)
        text = f"👤 **PROFILE SYSTEM DATA**\n\n🆔 User ID: `{user_id}`\n💰 Available Balance: ₹{user_record['balance']:.2f}\n📅 Verified Status: Active Node"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=render_back_navigation_markup())

    elif data == "ui_how_to_use":
        guide_text = (
            "📖 **HOW TO USE THE BOT — SERVICE CORE**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "1️⃣ **Funds Add Karein:**\n"
            "   • `⚡ Add Fund (Auto)` use karein dynamic QR generation ke liye.\n"
            "   • `💼 Manual Deposit` se payment karke UTR verification pipeline me bhein.\n\n"
            "2️⃣ **Purchase Key Structure:**\n"
            "   • Click `🛍️ Shop` and browse listed products.\n"
            "   • Select item and duration plan to complete instant execution.\n\n"
            "3️⃣ **Inventory Recovery:**\n"
            "   • Aapki items humesha `🔑 My Keys` node ke andar secured logged rahengi."
        )
        await query.edit_message_text(guide_text, parse_mode="Markdown", reply_markup=render_back_navigation_markup())

    elif data == "ui_my_keys":
        user_record = initialize_user_registers(user_id)
        keys_list = user_record.get('purchased_keys', [])
        if not keys_list:
            await query.edit_message_text("📂 **INVENTORY SYSTEM NODE**\n\nAapne abhi tak koi key purchase nahi ki hai.", reply_markup=render_back_navigation_markup())
            return
        txt = "🔑 **YOUR SECURED STOCK ARCHIVE** 🔑\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, k_info in enumerate(keys_list, 1):
            txt += f"{i}. 📦 Item: `{k_info['item']}`\n   🔑 Key: `{k_info['key']}`\n   📅 Date: {k_info['date']}\n\n"
        await query.edit_message_text(txt, parse_mode="Markdown", reply_markup=render_back_navigation_markup())

    # --- INITIALIZE MATRIX GRID DIALPADS ---
    elif data in ["ui_route_manual", "ui_route_auto"]:
        mode = "manual" if data == "ui_route_manual" else "auto"
        context.user_data['dial_string'] = ""
        mode_title = "💼 MANUAL CHECKOUT" if mode == "manual" else "⚡ AUTOMATED CHECKOUT"
        await query.edit_message_text(
            f"💰 **{mode_title} ENGINE**\n\nEnter Amount via Dynamic Grid UI Node:\n\n👉 Current Amount: `₹0`",
            parse_mode="Markdown", reply_markup=render_matrix_dialpad(mode)
        )

    # --- DIALPAD PROCESSING STRATAGEM ---
    elif data.startswith("pad_"):
        parts = data.split("_")
        mode, action = parts[1], parts[2]
        current_str = context.user_data.get('dial_string', "")
        mode_title = "💼 MANUAL DEPOSIT NODE" if mode == "manual" else "⚡ AUTOMATED DYNAMIC NODE"
        
        if action.isdigit() or action == "10":
            current_str += action
            context.user_data['dial_string'] = current_str
            try: await query.edit_message_text(f"💰 **{mode_title}**\n\nEnter Amount:\n\n👉 Current Amount: `₹{current_str}`", parse_mode="Markdown", reply_markup=render_matrix_dialpad(mode))
            except Exception: pass
        elif action == "backspace":
            if current_str: current_str = current_str[:-1]
            context.user_data['dial_string'] = current_str
            display = current_str if current_str else "0"
            try: await query.edit_message_text(f"💰 **{mode_title}**\n\nEnter Amount:\n\n👉 Current Amount: `₹{display}`", parse_mode="Markdown", reply_markup=render_matrix_dialpad(mode))
            except Exception: pass
        elif action == "commit":
            if not current_str or int(current_str) <= 0: return
            final_amount = int(current_str)
            try: await query.message.delete()
            except Exception: pass
            
            if mode == "manual":
                context.user_data['state_route'] = 'EXPECTING_MANUAL_UTR'
                context.user_data['pending_deposit_amt'] = float(final_amount)
                await context.bot.send_photo(chat_id=chat_id, photo=QR_IMAGE_URL, caption=f"💰 **Manual Deposit Amount Requested:** `₹{final_amount}.00`\n\nScan dynamic QR destination node and send your clear 12-digit payment UTR reference string block below:")
            else:
                processing_msg = await context.bot.send_message(chat_id=chat_id, text=f"🔄 **Generating Live Secured QR Code for ₹{final_amount}...**")
                request_api_url = f"{API_BASE_URL}/qr.php?upi={MERCHANT_UPI_ID}&amount={final_amount}"
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(request_api_url, timeout=15) as response:
                            if response.status == 200:
                                payload = await response.json()
                                if payload.get("status") == "success":
                                    core_data = payload.get("data", {})
                                    live_qr_link = core_data.get("qr_url")
                                    caption = f"🚀 **DYNAMIC AUTO QR GATEWAY OPERATIONAL** 🚀\n\n💰 Requested Core Amount: `₹{final_amount}.00`\n\nScan and verify transaction, systems will credit wallet nodes automated within 2-3 seconds framework!"
                                    try: await processing_msg.delete()
                                    except Exception: pass
                                    await context.bot.send_photo(chat_id=chat_id, photo=live_qr_link, caption=caption, parse_mode="Markdown", reply_markup=render_back_navigation_markup())
                                    return
                    except Exception: pass
                await context.bot.send_message(chat_id=chat_id, text="❌ Automated execution gateway down! Please rely on Manual deposit modules.", reply_markup=render_back_navigation_markup())

    # --- USER CLIENT SHOP ENGINE RENDER LOGIC ---
    elif data == "ui_shop_cats":
        cats = SmartDatabaseRouter.get_node('categories') or {}
        buttons = []
        for cid, cdata in cats.items():
            buttons.append([InlineKeyboardButton(cdata['name'], callback_data=f"user_browse_cat_{cid}")])
        buttons.append([InlineKeyboardButton("🔙 Back to Main Matrix Menu", callback_data="back_main")])
        await query.edit_message_text("🛍️ **ACTIVE SYSTEM SERVICE CATALOG:**", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("user_browse_cat_"):
        cid = data.split("_")[3]
        cat_node = SmartDatabaseRouter.get_node(f'categories/{cid}') or {}
        products = cat_node.get('products', {})
        if not products:
            await query.edit_message_text("❌ There are currently no active items deployed inside this node.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="ui_shop_cats")]]))
            return
        buttons = []
        for pid, pdata in products.items():
            # 📦 EMOJI TO EVERY PRODUCT ACCORDING TO REQUIREMENT
            buttons.append([InlineKeyboardButton(f"📦 {pdata['name']}", callback_data=f"user_browse_days_{cid}_{pid}")])
        buttons.append([InlineKeyboardButton("🔙 Back to Catalog", callback_data="ui_shop_cats")])
        await query.edit_message_text(f"📁 **Category: {cat_node.get('name')}**\n\nSelect a product item:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("user_browse_days_"):
        parts = data.split("_")
        cid, pid = parts[3], parts[4]
        prod_node = SmartDatabaseRouter.get_node(f'categories/{cid}/products/{pid}') or {}
        plans = prod_node.get('plans', {})
        if not plans:
            await query.edit_message_text("❌ No license durations plans added by administration yet.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"user_browse_cat_{cid}")]]))
            return
        buttons = []
        for day, price in plans.items():
            emoji = get_day_emoji(str(day)) # PREMIUM DYNAMIC CUSTOM EMOJI FOR VALIDITY DAYS
            buttons.append([InlineKeyboardButton(f"{emoji} Validity: {day} Days - Cost: ₹{price:.2f}", callback_data=f"user_buy_key_node_{cid}_{pid}_{day}")])
        buttons.append([InlineKeyboardButton("🔙 Back to Products", callback_data=f"user_browse_cat_{cid}")])
        await query.edit_message_text(f"📦 **Product: {prod_node.get('name')}**\n\nSelect plan duration layout node:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("user_buy_key_node_"):
        parts = data.split("_")
        cid, pid, day = parts[4], parts[5], parts[6]
        prod_node = SmartDatabaseRouter.get_node(f'categories/{cid}/products/{pid}') or {}
        price = float(prod_node['plans'][day])
        user_record = initialize_user_registers(user_id)
        
        keys_pool = prod_node.get('keys', {}).get(day, [])
        
        if not keys_pool:
            await query.edit_message_text("❌ **NO STOCK AVAILABLE!** Required serial key tier is vacant. Please try again later or alert admin.", reply_markup=render_back_navigation_markup())
            return

        if user_record['balance'] < price:
            needed_amount = int(price - user_record['balance'])
            processing_msg = await context.bot.send_message(chat_id=chat_id, text=f"⚠️ **Insufficient Balance!** Generating Dynamic Checkout QR for ₹{needed_amount}...")
            
            request_api_url = f"{API_BASE_URL}/qr.php?upi={MERCHANT_UPI_ID}&amount={needed_amount}"
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(request_api_url, timeout=15) as response:
                        if response.status == 200:
                            payload = await response.json()
                            if payload.get("status") == "success":
                                live_qr_link = payload.get("data", {}).get("qr_url")
                                caption = (
                                    f"⚠️ **INSUFFICIENT FUNDS GATEWAY** ⚠️\n━━━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"📦 **Product:** `{prod_node['name']}`\n"
                                    f"⏳ **Duration:** `{day} Days`\n"
                                    f"💰 **Total Price:** ₹{price:.2f}\n"
                                    f"💳 **Required Extra Funds:** `₹{needed_amount}.00`\n\n"
                                    f"👉 Scan below QR to pay exactly `₹{needed_amount}`. Payment verify hote hi aapka wallet reload ho jayega!"
                                )
                                try: await processing_msg.delete()
                                except Exception: pass
                                try: await query.message.delete()
                                except Exception: pass
                                await context.bot.send_photo(chat_id=chat_id, photo=live_qr_link, caption=caption, parse_mode="Markdown", reply_markup=render_back_navigation_markup())
                                return
                except Exception: pass
            await context.bot.send_message(chat_id=chat_id, text="❌ Checkout gateway error. Manual deposit use karein.", reply_markup=render_back_navigation_markup())
            return
            
        selected_serial_key = keys_pool.pop(0)
        SmartDatabaseRouter.set_node(f'categories/{cid}/products/{pid}/keys/{day}', keys_pool)
        process_wallet_balance_mutation(user_id, -price)
        
        ldb = load_local_db()
        ldb["users"][str(user_id)]["purchased_keys"].append({
            "item": f"{prod_node['name']} ({day} Days)",
            "key": selected_serial_key,
            "date": str(datetime.date.today())
        })
        ldb["stats"]["total_sold_keys"] += 1
        ldb["stats"]["total_revenue"] += price
        save_local_db(ldb)
        
        await query.message.reply_text(
            f"🎉 **PURCHASE SUCCESSFUL!** 🎉\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 **Item:** `{prod_node['name']}`\n"
            f"⏱️ **Validity:** `{day} Days`\n"
            f"🔑 **Your Key:** `{selected_serial_key}`\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"ℹ️ *Ye key aapke 'My Keys' node me safe save ho gayi hai.*",
            parse_mode="Markdown", reply_markup=render_back_navigation_markup()
        )

        global_alert = (
            f"🔔 **NEW SHOP TRANSACTION NODE DETECTED** 🔔\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🛍️ **Product Name:** `{prod_node['name']}`\n"
            f"⏱️ **Duration Plan:** `{day} Days`\n"
            f"✅ **Status:** Successfully Dispatched from Stock\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ High-Speed Auto Checkout Core Active!"
        )
        users_pool = list(ldb.get("users", {}).keys())
        for target_uid in users_pool:
            if int(target_uid) != ADMIN_ID:
                try: await context.bot.send_message(chat_id=int(target_uid), text=global_alert, parse_mode="Markdown")
                except Exception: pass

        admin_alert = (
            f"👑 **ADMIN DEEP AUDIT SUCCESS LOG**\n"
            f"👤 User Unique ID: `{user_id}`\n"
            f"📛 Username: @{username}\n"
            f"📦 Item: `{prod_node['name']}` ({day} Days)\n"
            f"💵 Price Deducted: ₹{price}\n"
            f"🔑 Key Delivered: `{selected_serial_key}`"
        )
        try: await context.bot.send_message(chat_id=ADMIN_ID, text=admin_alert)
        except Exception: pass
        return

    # ==========================================
    # 👑 ADMINISTRATIVE MODULES
    # ==========================================
    if user_id != ADMIN_ID: return
    
    if data == "back_to_admin":
        await query.edit_message_text("⚡ **MASTER ADMINISTRATIVE INTERFACE PANEL** ⚡", reply_markup=render_admin_panel_keyboard())
    elif data == "adm_close_panel":
        await query.message.delete()
    elif data == "adm_view_stats":
        db = load_local_db()
        stats_text = f"📊 **ANALYTICS COMPONENT DISPLAY**\n\n👥 Registered User Nodes: `{len(db['users'])}`\n🔑 Key Transactions Sold: `{db['stats']['total_sold_keys']}`\n💰 Total Gross Volume: `₹{db['stats']['total_revenue']:.2f}`"
        await query.edit_message_text(stats_text, parse_mode="Markdown", reply_markup=render_admin_back_markup())
    elif data == "adm_manage_bal_menu":
        await query.edit_message_text("💰 **Balance Management Hub Console**", reply_markup=render_admin_balance_actions_keyboard())
    elif data == "adm_bal_check":
        context.user_data['admin_state'] = 'CHECK_BAL'
        await query.edit_message_text("🔍 Enter Target user unique telegram ID numerical sequence:", reply_markup=render_admin_back_markup())
    elif data == "adm_bal_add":
        context.user_data['admin_state'] = 'BAL_ADD'
        await query.edit_message_text("➕ **Credit Balance Matrix**\n\nSend data payload configuration syntax:\n`USER_ID|AMOUNT`", reply_markup=render_admin_back_markup())
    elif data == "adm_bal_remove":
        context.user_data['admin_state'] = 'BAL_REM'
        await query.edit_message_text("➖ **Debit Balance Matrix**\n\nSend data payload configuration syntax:\n`USER_ID|AMOUNT`", reply_markup=render_admin_back_markup())
    
    elif data == "adm_trigger_bc":
        context.user_data['admin_state'] = 'BC_MEDIA_STREAM'
        await query.edit_message_text("📢 **MULTIMEDIA BROADCAST ROUTER**\n\nSend **ANYTHING**. Bot will broadcast live safely to all users.", reply_markup=render_admin_back_markup())

    elif data == "adm_manage_cats":
        cats = SmartDatabaseRouter.get_node('categories') or {}
        buttons = []
        for cid, cdata in cats.items():
            buttons.append([InlineKeyboardButton(f"📁 {cdata['name']}", callback_data=f"adm_cat_node_{cid}")])
        buttons.append([InlineKeyboardButton("🔙 Back Dashboard", callback_data="back_to_admin")])
        await query.edit_message_text("🗂️ **SELECT CLUSTER CATEGORY COMPARTMENT:**", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("adm_cat_node_"):
        cid = data.split("_")[3]
        cat_node = SmartDatabaseRouter.get_node(f'categories/{cid}') or {}
        await query.edit_message_text(f"🛠️ **Category Panel Management:** \n🏷️ Name: *{cat_node.get('name')}*\n🆔 Cluster ID: `{cid}`\n\nConfigure structural attributes nodes below:", parse_mode="Markdown", reply_markup=render_admin_category_management_markup(cid))

    elif data.startswith("adm_list_prods_"):
        cid = data.split("_")[3]
        prods = SmartDatabaseRouter.get_node(f'categories/{cid}/products') or {}
        if not prods: text = "📂 No structural items active inside database tree configuration layout."
        else:
            text = "📋 **DEPLOYED INTERNAL PRODUCTS MANAGEMENT REGISTRY:**\n\n"
            for pid, pdata in prods.items():
                text += f"📦 ID: `{pid}` | Name: **{pdata['name']}**\n"
                plans = pdata.get('plans', {})
                for day, rate in plans.items():
                    k_len = len(pdata.get('keys', {}).get(day, []))
                    emoji = get_day_emoji(str(day))
                    text += f" └── {emoji} Plan `{day}` Days ➔ Cost: ₹{rate:.2f} | Stock Pool: [{k_len} Keys]\n"
                text += "\n"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Return", callback_data=f"adm_cat_node_{cid}")]]))

    elif data.startswith("adm_seq_addprod_"):
        cid = data.split("_")[3]
        context.user_data['admin_state'] = f"SEQ_ADD_PROD_NAME|{cid}"
        await query.edit_message_text("➕ **ADD PRODUCT (Step 1/1):**\n\nNaye Product ka display name text send karein:")

    elif data.startswith("adm_seq_remprod_"):
        cid = data.split("_")[3]
        context.user_data['admin_state'] = f"SEQ_REM_PROD_ALL|{cid}"
        await query.edit_message_text("🗑️ **REMOVE PRODUCT COMPONENT (Danger Node):**\n\nJis product ko poori tarah delete karna hai uska unique ID/Name send karein:")

    elif data.startswith("adm_seq_adddays_"):
        cid = data.split("_")[3]
        context.user_data['admin_state'] = f"SEQ_ADD_DAYS_NAME|{cid}"
        await query.edit_message_text("⏱️ **ADD VALIDITY DAYS (Step 1/3):**\n\nProduct ka ID/Name send karein jisme days jodna hai:")

    elif data.startswith("adm_seq_remdays_"):
        cid = data.split("_")[3]
        context.user_data['admin_state'] = f"SEQ_REM_DAYS_ALL|{cid}"
        await query.edit_message_text("🗑️ **REMOVE VALIDITY DAYS:**\n\nProduct name aur Target days configuration sequence dalo jise delete krna hai:\nSyntax: `PRODUCT_ID|DAYS`")

    elif data.startswith("adm_seq_addkey_"):
        cid = data.split("_")[3]
        context.user_data['admin_state'] = f"SEQ_ADD_KEY_NAME|{cid}"
        await query.edit_message_text("🔑 **LOAD LICENSE SERIAL KEY (Step 1/3):**\n\nProduct unique ID/Name send karein:")

    elif data.startswith("adm_seq_remkey_"):
        cid = data.split("_")[3]
        context.user_data['admin_state'] = f"SEQ_REM_KEY_ALL|{cid}"
        await query.edit_message_text("🗑️ **PURGE ALL STOCK KEYS:**\n\nProduct name aur days cluster send karein jiske saare keys empty krne hain:\nSyntax: `PRODUCT_ID|DAYS`")

    elif data.startswith("adm_check_keys_"):
        cid = data.split("_")[3]
        prods = SmartDatabaseRouter.get_node(f'categories/{cid}/products') or {}
        text = "🔎 **STOCK LOG FILE EVALUATOR SYSTEM:**\n\n"
        for pid, pdata in prods.items():
            text += f"📦 Product: *{pdata['name']}*\n"
            keys_node = pdata.get('keys', {})
            for d, klist in keys_node.items():
                emoji = get_day_emoji(str(d))
                text += f" └── {emoji} Plan {d} Days ➔ Available Stock Pool: `{len(klist)}` Available Keys\n"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Return Node", callback_data=f"adm_cat_node_{cid}")]]))

# ==========================================
# 📥 INBOUND DATA STREAM MULTIPLEXER
# ==========================================
async def global_inbound_stream_multiplexer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    adm_state = context.user_data.get('admin_state')
    
    if user_id == ADMIN_ID and adm_state == 'BC_MEDIA_STREAM':
        context.user_data['admin_state'] = None
        db = load_local_db()
        users_pool = list(db.get("users", {}).keys())
        dispatch_count = 0
        status_banner = await update.message.reply_text(f"⏳ Broadcast process initialized...")
        for target_uid in users_pool:
            try:
                await update.message.forward(chat_id=int(target_uid))
                dispatch_count += 1
            except Exception: continue
        await status_banner.edit_text(f"✅ **Dynamic Broadcast Matrix Successful!** Delivered safely to `{dispatch_count}` users.", reply_markup=render_admin_back_markup())
        return

    if user_id == ADMIN_ID and adm_state:
        text = update.message.text.strip() if update.message.text else ""
        
        if adm_state.startswith("SEQ_ADD_PROD_NAME|"):
            cid = adm_state.split("|")[1]
            context.user_data['admin_state'] = None
            pid = text.lower().replace(" ", "_")
            SmartDatabaseRouter.set_node(f'categories/{cid}/products/{pid}', {"name": text, "plans": {}, "keys": {}})
            await update.message.reply_text(f"✅ **Product Added:** `{text}` successfully created!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Return", callback_data=f"adm_cat_node_{cid}")]]))
            return

        elif adm_state.startswith("SEQ_REM_PROD_ALL|"):
            cid = adm_state.split("|")[1]
            context.user_data['admin_state'] = None
            pid = text.lower().replace(" ", "_")
            SmartDatabaseRouter.delete_node(f'categories/{cid}/products/{pid}')
            await update.message.reply_text(f"🗑️ Product node structure completely dropped.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Return", callback_data=f"adm_cat_node_{cid}")]]))
            return

        elif adm_state.startswith("SEQ_ADD_DAYS_NAME|"):
            parts = adm_state.split("|")
            cid = parts[1]
            pid = text.lower().replace(" ", "_")
            prod = SmartDatabaseRouter.get_node(f'categories/{cid}/products/{pid}')
            if not prod:
                await update.message.reply_text("❌ Product ID invalid! Operation closed.")
                context.user_data['admin_state'] = None
                return
            context.user_data['admin_state'] = f"SEQ_ADD_DAYS_COUNT|{cid}|{pid}"
            await update.message.reply_text(f"⏱️ **ADD VALIDITY DAYS (Step 2/3):**\n\nProduct: `{prod['name']}`\n\nAb kitne DAYS add karni hai (e.g. `30` ya `7`), send karein:")
            return

        elif adm_state.startswith("SEQ_ADD_DAYS_COUNT|"):
            parts = adm_state.split("|")
            cid, pid = parts[1], parts[2]
            context.user_data['admin_state'] = f"SEQ_ADD_DAYS_PRICE|{cid}|{pid}|{text}"
            await update.message.reply_text(f"⏱️ **ADD VALIDITY DAYS (Step 3/3):**\n\nDays Target: `{text} Days`\n\nAb is duration plan ke liye PRICE (INR me) send karein:")
            return

        elif adm_state.startswith("SEQ_ADD_DAYS_PRICE|"):
            parts = adm_state.split("|")
            cid, pid, days = parts[1], parts[2], parts[3]
            context.user_data['admin_state'] = None
            try:
                price_val = float(text)
                SmartDatabaseRouter.set_node(f'categories/{cid}/products/{pid}/plans/{days}', price_val)
                await update.message.reply_text(f"✅ **Plan Configured Successfully!**\n\nPlan duration mapped to `{days} Days` with cost set at `₹{price_val}`.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Return", callback_data=f"adm_cat_node_{cid}")]]))
            except Exception: await update.message.reply_text("❌ Price evaluation float mismatch error.")
            return

        elif adm_state.startswith("SEQ_REM_DAYS_ALL|"):
            cid = adm_state.split("|")[1]
            context.user_data['admin_state'] = None
            try:
                pid, day = text.split("|")[0].strip().lower().replace(" ", "_"), text.split("|")[1].strip()
                SmartDatabaseRouter.delete_node(f'categories/{cid}/products/{pid}/plans/{day}')
                SmartDatabaseRouter.delete_node(f'categories/{cid}/products/{pid}/keys/{day}')
                await update.message.reply_text("🗑️ Sub-plan nodes purged cleanly.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Return", callback_data=f"adm_cat_node_{cid}")]]))
            except Exception: await update.message.reply_text("❌ Syntax validation failure formatting error.")
            return

        elif adm_state.startswith("SEQ_ADD_KEY_NAME|"):
            parts = adm_state.split("|")
            cid = parts[1]
            pid = text.lower().replace(" ", "_")
            prod = SmartDatabaseRouter.get_node(f'categories/{cid}/products/{pid}')
            if not prod:
                await update.message.reply_text("❌ Product target missing.")
                context.user_data['admin_state'] = None
                return
            context.user_data['admin_state'] = f"SEQ_ADD_KEY_DAYS|{cid}|{pid}"
            await update.message.reply_text(f"🔑 **LOAD LICENSE SERIAL KEY (Step 2/3):**\n\nProduct: `{prod['name']}`\n\nKis validity duration pool me key load karni hai (Days count dalo, e.g. `30`):")
            return

        elif adm_state.startswith("SEQ_ADD_KEY_DAYS|"):
            parts = adm_state.split("|")
            cid, pid = parts[1], parts[2]
            context.user_data['admin_state'] = f"SEQ_ADD_KEY_STRING|{cid}|{pid}|{text}"
            await update.message.reply_text(f"🔑 **LOAD LICENSE SERIAL KEY (Step 3/3):**\n\nTarget Pool: `{text} Days`\n\nAb apni actual SERIAL LICENSE KEY string send karein:")
            return

        elif adm_state.startswith("SEQ_ADD_KEY_STRING|"):
            parts = adm_state.split("|")
            cid, pid, days = parts[1], parts[2], parts[3]
            context.user_data['admin_state'] = None
            current_keys = SmartDatabaseRouter.get_node(f'categories/{cid}/products/{pid}/keys/{days}') or []
            current_keys.append(text)
            SmartDatabaseRouter.set_node(f'categories/{cid}/products/{pid}/keys/{days}', current_keys)
            await update.message.reply_text(f"✅ **Key Array Loaded Successfully!**\n\nCurrent stock: `[{len(current_keys)} Keys]`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Return", callback_data=f"adm_cat_node_{cid}")]]))
            return

        elif adm_state.startswith("SEQ_REM_KEY_ALL|"):
            cid = adm_state.split("|")[1]
            context.user_data['admin_state'] = None
            try:
                pid, day = text.split("|")[0].strip().lower().replace(" ", "_"), text.split("|")[1].strip()
                SmartDatabaseRouter.set_node(f'categories/{cid}/products/{pid}/keys/{day}', [])
                await update.message.reply_text("🗑️ Target stock pool keys completely reset.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Return", callback_data=f"adm_cat_node_{cid}")]]))
            except Exception: await update.message.reply_text("❌ Structure syntax logic error.")
            return

        elif adm_state == 'CHECK_BAL':
            context.user_data['admin_state'] = None
            node = SmartDatabaseRouter.get_node(f'users/{text}')
            if node: await update.message.reply_text(f"👤 User: `{text}`\n💰 Wallet Balance: ₹{node.get('balance', 0.0):.2f}", reply_markup=render_admin_back_markup())
            else: await update.message.reply_text("❌ Missing user node inside database.", reply_markup=render_admin_back_markup())
            return
        elif adm_state in ['BAL_ADD', 'BAL_REM']:
            context.user_data['admin_state'] = None
            try:
                parts = text.split("|")
                tgt_id, amt = parts[0].strip(), float(parts[1].strip())
                multiplier = 1 if adm_state == 'BAL_ADD' else -1
                new_balance = process_wallet_balance_mutation(tgt_id, multiplier * amt)
                await update.message.reply_text(f"✅ Transaction processed. Updated Balance: ₹{new_balance:.2f}", reply_markup=render_admin_back_markup())
            except Exception: await update.message.reply_text("❌ Verification fault logic exception.")
            return

    state = context.user_data.get('state_route')
    if state == 'EXPECTING_MANUAL_UTR':
        context.user_data['manual_deposit_utr'] = text
        context.user_data['state_route'] = 'EXPECTING_MANUAL_SCREENSHOT'
        await update.message.reply_text("📸 Reference hash recorded. Send payment screenshot file now:")
    elif state == 'EXPECTING_MANUAL_SCREENSHOT':
        if not update.message.photo: return
        context.user_data['state_route'] = None
        screenshot_file_id = update.message.photo[-1].file_id
        utr_ref = context.user_data.get('manual_deposit_utr')
        deposit_amt = context.user_data.get('pending_deposit_amt', 0.0)
        admin_payload = f"📥 **NEW MANUAL DEPOSIT PIPELINE CLAIM**\n\n👤 User Node: `{user_id}`\n💰 Sum Claimed: ₹{deposit_amt:.2f}\n📝 Reference UTR String: `{utr_ref}`"
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=screenshot_file_id, caption=admin_payload)
        await update.message.reply_text("⏳ Verification packet dispatched successfully to admin panel logs.", reply_markup=render_back_navigation_markup())

def main() -> None:
    load_local_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command_handler))
    app.add_handler(CommandHandler("admin", admin_panel_launcher))
    app.add_handler(CallbackQueryHandler(global_callback_routing_engine))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, global_inbound_stream_multiplexer))
    logger.info("🤖 SYSTEM OPERATIONAL - Fixed v8.1 Engine Live.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
