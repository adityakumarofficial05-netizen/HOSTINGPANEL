import os
import re
import json
import time
import html
import logging
import threading
from datetime import datetime, timedelta
from urllib.parse import quote

import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===================== CONFIG =====================
BOT_TOKEN = "8985901508:AAHKEPNFfCgyY9FVwrh1EzqnRF4-8i9vKp4"
ADMIN_ID = 8360629421

API_KEY = ""
BASE_API = 
CREATE_API = BASE_API + "/create-username={username}=password={password}?key=" + API_KEY + "&date={date}"
USERS_API = BASE_API + "/users?key=" + API_KEY
DELETE_API = BASE_API + "/delete-user={username}?key=" + API_KEY
LOGIN_URL = "http://tgbot-hosting.onrender.com"

UPI_ID = "madeshkumar51@fam"
QR_API = "https://fampay.anujbots.xyz/qr.php"
VERIFY_API = "https://fampay.anujbots.xyz/verify.php"
VERIFY_KEY = "FAM_7d2964d9ebb2cfdf551be839df6aee6943e90732e8574a63"

SUPPORT_URL = "http://t.me/ADI_HOSTING_BOT"
DATA_FILE = "data.json"

PLANS = {
    "day": {"title": "1 Day Hosting", "price": 10, "days": 1, "icon": "⚡"},
    "permanent": {"title": "Permanent Hosting", "price": 40, "days": 3650, "icon": "👑"},
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
lock = threading.RLock()
user_steps = {}
pending_orders = {}

# ===================== DATA =====================
def default_data():
    return {"users": {}, "balances": {}, "sales": 0, "payments": [], "accounts": []}


def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data(), f, indent=4)
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = default_data()
    for k, v in default_data().items():
        d.setdefault(k, v)
    return d


data = load_data()


def save_data():
    with lock:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


def save_user(user):
    sid = str(user.id)
    with lock:
        data["users"][sid] = {
            "id": user.id,
            "name": user.first_name or "User",
            "username": user.username or "",
            "joined": int(time.time()),
        }
        save_data()

# ===================== HELPERS =====================
def esc(x):
    return html.escape(str(x))


def expiry_for_plan(plan_id):
    return (datetime.now() + timedelta(days=PLANS[plan_id]["days"])).strftime("%Y-%m-%d")


def is_valid_username(username):
    return re.fullmatch(r"[A-Za-z0-9_]{3,20}", username or "") is not None


def menu_markup(uid):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("⚡ BUY 1 DAY · ₹10", callback_data="buy_day"),
        InlineKeyboardButton("👑 BUY PERMANENT · ₹40", callback_data="buy_permanent"),
    )
    kb.add(
        InlineKeyboardButton("💰 WALLET", callback_data="wallet"),
        InlineKeyboardButton("👤 PROFILE", callback_data="profile"),
    )
    kb.add(
        InlineKeyboardButton("📋 MY ACCOUNTS", callback_data="accounts"),
        InlineKeyboardButton("🆘 SUPPORT", url=SUPPORT_URL),
    )
    if uid == ADMIN_ID:
        kb.add(InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin"))
    return kb


def back_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🏠 BACK TO MENU", callback_data="home"))
    return kb


def pay_markup(plan_id):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💰 PAY WITH WALLET", callback_data=f"wallet_{plan_id}"),
        InlineKeyboardButton("💳 GENERATE QR PAYMENT", callback_data=f"qr_{plan_id}"),
        InlineKeyboardButton("🏠 BACK TO MENU", callback_data="home"),
    )
    return kb


def admin_markup():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ CREATE USER", callback_data="admin_create"),
        InlineKeyboardButton("👥 API USERS", callback_data="admin_users"),
    )
    kb.add(
        InlineKeyboardButton("🗑 DELETE USER", callback_data="admin_delete"),
        InlineKeyboardButton("💳 ADD BALANCE", callback_data="admin_addbal"),
    )
    kb.add(
        InlineKeyboardButton("➖ REMOVE BAL", callback_data="admin_removebal"),
        InlineKeyboardButton("📊 STATS", callback_data="stats"),
    )
    kb.add(InlineKeyboardButton("🏠 BACK TO MENU", callback_data="home"))
    return kb


def main_text(user):
    sid = str(user.id)
    bal = data["balances"].get(sid, 0)
    name = user.first_name or "User"
    return f"""
<b>☁️ NEXA CLOUD</b>
<i>Python Bot Hosting Store</i>

━━━━━━━━━━━━━━━━━━━━
👋 <b>{esc(name)}</b>
🆔 <code>{sid}</code>
💰 Wallet: <b>₹{bal}</b>
━━━━━━━━━━━━━━━━━━━━

⚡ <b>1 Day Hosting</b> — ₹10
👑 <b>Permanent Hosting</b> — ₹40

🟢 Instant account creation
🟢 Username & password by user
🟢 Wallet + QR payment
🟢 Clean expiry date system

<b>Choose one button below 👇</b>
"""


def plan_text(plan_id, uid):
    p = PLANS[plan_id]
    bal = data["balances"].get(str(uid), 0)
    exp = "Tomorrow" if plan_id == "day" else "Long Validity"
    return f"""
<b>{p['icon']} {esc(p['title'])}</b>

━━━━━━━━━━━━━━━━━━━━
💸 Price: <b>₹{p['price']}</b>
💰 Wallet: <b>₹{bal}</b>
📅 Expiry: <b>{exp}</b>
━━━━━━━━━━━━━━━━━━━━

<b>Select payment method:</b>
"""


def format_create_response(result, username, password, expiry_date):
    try:
        js = json.loads(result) if isinstance(result, str) else result
        ok = bool(js.get("ok") or js.get("status"))
        msg = js.get("message", "User created" if ok else "Create failed")
        username = js.get("username", username)
        password = js.get("password", password)
        expiry_date = js.get("expiry_date", expiry_date)
    except Exception:
        ok = True
        msg = "Account created"

    if ok:
        return f"""
<b>✅ ACCOUNT CREATED</b>

━━━━━━━━━━━━━━━━━━━━
👤 Username:
<code>{esc(username)}</code>

🔑 Password:
<code>{esc(password)}</code>

📅 Expiry Date:
<code>{esc(expiry_date)}</code>

🌐 Login Panel:
{LOGIN_URL}
━━━━━━━━━━━━━━━━━━━━

🎉 <b>{esc(msg)}</b>
"""
    return f"""
<b>❌ ACCOUNT CREATE FAILED</b>

━━━━━━━━━━━━━━━━━━━━
⚠️ Message:
<code>{esc(msg)}</code>
━━━━━━━━━━━━━━━━━━━━
"""


def send_or_edit(call, text, markup=None):
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

# ===================== API CALLS =====================
def create_user_api(username, password, date):
    try:
        url = CREATE_API.format(username=quote(username), password=quote(password), date=quote(date))
        r = requests.get(url, timeout=25)
        logging.info("CREATE API: %s", r.text)
        return True, r.text
    except Exception as e:
        logging.error("CREATE ERROR: %s", e)
        return False, str(e)


def users_api():
    try:
        r = requests.get(USERS_API, timeout=25)
        logging.info("USERS API: %s", r.text)
        return True, r.text
    except Exception as e:
        return False, str(e)


def delete_user_api(username):
    try:
        url = DELETE_API.format(username=quote(username))
        r = requests.get(url, timeout=25)
        logging.info("DELETE API: %s", r.text)
        return True, r.text
    except Exception as e:
        return False, str(e)


def generate_qr(amount):
    try:
        url = f"{QR_API}?upi={quote(UPI_ID)}&amount={amount}"
        r = requests.get(url, timeout=20)
        logging.info("QR API: %s", r.text)
        js = r.json()
        order_id = js.get("order_id") or js.get("data", {}).get("order_id") or js.get("result", {}).get("order_id")
        qr_url = js.get("qr_url") or js.get("data", {}).get("qr_url") or js.get("result", {}).get("qr_url") or js.get("qr") or js.get("image")
        return order_id, qr_url, js
    except Exception as e:
        logging.error("QR ERROR: %s", e)
        return None, None, None


def verify_payment(order_id):
    try:
        url = f"{VERIFY_API}?order_id={quote(order_id)}&api_key={quote(VERIFY_KEY)}"
        r = requests.get(url, timeout=15)
        logging.info("VERIFY API: %s", r.text)
        js = r.json()
        status = str(js.get("status", "pending")).lower()
        if status in ["success", "paid", "completed"]:
            return "success", js
        if status in ["failed", "fail", "cancelled", "expired"]:
            return "failed", js
        return "pending", js
    except Exception as e:
        logging.error("VERIFY ERROR: %s", e)
        return "pending", None

# ===================== COMMANDS =====================
@bot.message_handler(commands=["start", "menu"])
def start(m):
    save_user(m.from_user)
    bot.send_message(m.chat.id, main_text(m.from_user), reply_markup=menu_markup(m.from_user.id))


@bot.message_handler(commands=["admin"])
def admin_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return bot.reply_to(m, "❌ Access denied")
    bot.send_message(m.chat.id, "<b>👑 ADMIN DASHBOARD</b>\n\nChoose action below:", reply_markup=admin_markup())


@bot.message_handler(commands=["addbal"])
def addbal(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, uid, amt = m.text.split()
        amt = int(amt)
        with lock:
            data["balances"][uid] = data["balances"].get(uid, 0) + amt
            save_data()
        bot.reply_to(m, f"✅ Added ₹{amt} to <code>{uid}</code>")
    except Exception:
        bot.reply_to(m, "Use: <code>/addbal USER_ID AMOUNT</code>")


@bot.message_handler(commands=["removebal"])
def removebal(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, uid, amt = m.text.split()
        amt = int(amt)
        with lock:
            data["balances"][uid] = max(0, data["balances"].get(uid, 0) - amt)
            save_data()
        bot.reply_to(m, f"✅ Removed ₹{amt} from <code>{uid}</code>")
    except Exception:
        bot.reply_to(m, "Use: <code>/removebal USER_ID AMOUNT</code>")


@bot.message_handler(commands=["create"])
def create_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, username, password, date = m.text.split(maxsplit=3)
        ok, result = create_user_api(username, password, date)
        bot.reply_to(m, format_create_response(result, username, password, date), reply_markup=back_menu())
    except Exception:
        bot.reply_to(m, "Use: <code>/create USERNAME PASSWORD 2026-12-31</code>")


@bot.message_handler(commands=["delete"])
def delete_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, username = m.text.split(maxsplit=1)
        ok, result = delete_user_api(username)
        bot.reply_to(m, f"🗑 <b>DELETE RESULT</b>\n\n<code>{esc(result)}</code>")
    except Exception:
        bot.reply_to(m, "Use: <code>/delete USERNAME</code>")


@bot.message_handler(commands=["users"])
def users_cmd(m):
    if m.from_user.id != ADMIN_ID:
        return
    ok, result = users_api()
    t = esc(result)
    if len(t) > 3500:
        t = t[:3500] + "\n...more hidden..."
    bot.reply_to(m, f"👥 <b>API USERS</b>\n\n<code>{t}</code>")

# ===================== CALLBACKS =====================
@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    save_user(call.from_user)
    uid = call.from_user.id
    sid = str(uid)
    bot.answer_callback_query(call.id)

    if call.data == "home":
        send_or_edit(call, main_text(call.from_user), menu_markup(uid))

    elif call.data == "buy_day":
        send_or_edit(call, plan_text("day", uid), pay_markup("day"))

    elif call.data == "buy_permanent":
        send_or_edit(call, plan_text("permanent", uid), pay_markup("permanent"))

    elif call.data.startswith("wallet_"):
        plan_id = call.data.replace("wallet_", "")
        plan = PLANS[plan_id]
        bal = data["balances"].get(sid, 0)
        if bal < plan["price"]:
            return send_or_edit(call, f"❌ <b>LOW BALANCE</b>\n\nNeed: ₹{plan['price']}\nYour Wallet: ₹{bal}", back_menu())
        with lock:
            data["balances"][sid] = bal - plan["price"]
            data["sales"] += plan["price"]
            data["payments"].append({"user_id": sid, "plan": plan_id, "amount": plan["price"], "method": "wallet", "time": int(time.time())})
            save_data()
        user_steps[sid] = {"step": "username", "plan_id": plan_id}
        send_or_edit(call, "✅ <b>PAYMENT SUCCESS</b>\n\n👤 Send hosting username:", back_menu())

    elif call.data.startswith("qr_"):
        plan_id = call.data.replace("qr_", "")
        plan = PLANS[plan_id]
        order_id, qr_url, raw = generate_qr(plan["price"])
        if not order_id or not qr_url:
            return send_or_edit(call, "❌ QR generate failed. Try again.", back_menu())
        pending_orders[sid] = {"order_id": order_id, "plan_id": plan_id, "amount": plan["price"], "start": time.time()}
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        cap = f"""
<b>💳 QR PAYMENT</b>

━━━━━━━━━━━━━━━━━━━━
📦 Plan: <b>{esc(plan['title'])}</b>
💰 Amount: <b>₹{plan['price']}</b>
🆔 Order: <code>{esc(order_id)}</code>
━━━━━━━━━━━━━━━━━━━━

⚡ Auto checking every 5 seconds
⌛ Timeout 5 minutes
"""
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("🔄 CHECK PAYMENT", callback_data="checkpay"), InlineKeyboardButton("🏠 BACK TO MENU", callback_data="home"))
        bot.send_photo(call.message.chat.id, qr_url, caption=cap, reply_markup=kb)
        threading.Thread(target=payment_thread, args=(call.message.chat.id, sid), daemon=True).start()

    elif call.data == "checkpay":
        if sid not in pending_orders:
            return bot.answer_callback_query(call.id, "No pending payment", show_alert=True)
        status, _ = verify_payment(pending_orders[sid]["order_id"])
        bot.answer_callback_query(call.id, f"Status: {status}", show_alert=True)

    elif call.data == "wallet":
        bal = data["balances"].get(sid, 0)
        send_or_edit(call, f"<b>💰 WALLET</b>\n\nBalance: <b>₹{bal}</b>", back_menu())

    elif call.data == "profile":
        bal = data["balances"].get(sid, 0)
        send_or_edit(call, f"<b>👤 PROFILE</b>\n\nName: <b>{esc(call.from_user.first_name or 'User')}</b>\nID: <code>{sid}</code>\nWallet: <b>₹{bal}</b>", back_menu())

    elif call.data == "accounts":
        accs = [a for a in data["accounts"] if a.get("user_id") == sid]
        if not accs:
            txt = "📋 <b>MY ACCOUNTS</b>\n\nNo accounts yet."
        else:
            lines = ["📋 <b>MY ACCOUNTS</b>\n"]
            for a in accs[-10:]:
                lines.append(f"\n👤 <code>{esc(a.get('username'))}</code>\n📅 {esc(a.get('expiry'))}")
            txt = "".join(lines)
        send_or_edit(call, txt, back_menu())

    elif call.data == "admin":
        if uid != ADMIN_ID:
            return send_or_edit(call, "❌ Access denied", back_menu())
        send_or_edit(call, "<b>👑 ADMIN DASHBOARD</b>\n\nChoose action below:", admin_markup())

    elif call.data == "admin_create":
        if uid == ADMIN_ID:
            user_steps[sid] = {"step": "admin_username"}
            send_or_edit(call, "➕ <b>CREATE USER</b>\n\nSend username:", back_menu())

    elif call.data == "admin_delete":
        if uid == ADMIN_ID:
            user_steps[sid] = {"step": "delete_username"}
            send_or_edit(call, "🗑 <b>DELETE USER</b>\n\nSend username:", back_menu())

    elif call.data == "admin_users":
        if uid == ADMIN_ID:
            ok, result = users_api()
            t = esc(result)
            if len(t) > 3500:
                t = t[:3500] + "\n...more hidden..."
            send_or_edit(call, f"👥 <b>API USERS</b>\n\n<code>{t}</code>", back_menu())

    elif call.data == "admin_addbal":
        send_or_edit(call, "Use command:\n<code>/addbal USER_ID AMOUNT</code>", back_menu())

    elif call.data == "admin_removebal":
        send_or_edit(call, "Use command:\n<code>/removebal USER_ID AMOUNT</code>", back_menu())

    elif call.data == "stats":
        if uid == ADMIN_ID:
            send_or_edit(call, f"📊 <b>STATS</b>\n\nUsers: <b>{len(data['users'])}</b>\nSales: <b>₹{data['sales']}</b>\nPayments: <b>{len(data['payments'])}</b>\nAccounts: <b>{len(data['accounts'])}</b>", back_menu())

# ===================== PAYMENT =====================
def payment_thread(chat_id, sid):
    order = pending_orders.get(sid)
    if not order:
        return
    start = time.time()
    while time.time() - start < 300:
        order = pending_orders.get(sid)
        if not order:
            return
        status, raw = verify_payment(order["order_id"])
        if status == "success":
            pending_orders.pop(sid, None)
            plan_id = order["plan_id"]
            plan = PLANS[plan_id]
            with lock:
                data["sales"] += plan["price"]
                data["payments"].append({"user_id": sid, "plan": plan_id, "amount": plan["price"], "method": "qr", "order_id": order["order_id"], "time": int(time.time())})
                save_data()
            user_steps[sid] = {"step": "username", "plan_id": plan_id}
            bot.send_message(chat_id, "✅ <b>PAYMENT SUCCESS</b>\n\n👤 Send hosting username:", reply_markup=back_menu())
            return
        if status == "failed":
            pending_orders.pop(sid, None)
            bot.send_message(chat_id, "❌ Payment failed.", reply_markup=back_menu())
            return
        time.sleep(5)
    pending_orders.pop(sid, None)
    bot.send_message(chat_id, "⌛ Payment timeout.", reply_markup=back_menu())

# ===================== STEPS =====================
@bot.message_handler(func=lambda m: True)
def steps(m):
    sid = str(m.from_user.id)
    if sid not in user_steps:
        return
    step = user_steps[sid]["step"]
    txt = (m.text or "").strip()

    if step == "username":
        if not is_valid_username(txt):
            return bot.reply_to(m, "❌ Username 3-20 letters/numbers only.")
        user_steps[sid]["username"] = txt
        user_steps[sid]["step"] = "password"
        return bot.reply_to(m, "🔑 Send hosting password:")

    if step == "password":
        if len(txt) < 4:
            return bot.reply_to(m, "❌ Password minimum 4 characters.")
        username = user_steps[sid]["username"]
        password = txt
        plan_id = user_steps[sid]["plan_id"]
        expiry = expiry_for_plan(plan_id)
        ok, result = create_user_api(username, password, expiry)
        user_steps.pop(sid, None)
        if ok:
            with lock:
                data["accounts"].append({"user_id": sid, "username": username, "password": password, "plan": plan_id, "expiry": expiry, "time": int(time.time())})
                save_data()
        return bot.send_message(m.chat.id, format_create_response(result, username, password, expiry), reply_markup=back_menu())

    if step == "admin_username":
        if m.from_user.id != ADMIN_ID:
            return
        user_steps[sid] = {"step": "admin_password", "username": txt}
        return bot.reply_to(m, "🔑 Send password:")

    if step == "admin_password":
        if m.from_user.id != ADMIN_ID:
            return
        user_steps[sid]["password"] = txt
        user_steps[sid]["step"] = "admin_date"
        return bot.reply_to(m, "📅 Send expiry date, example: <code>2026-12-31</code>")

    if step == "admin_date":
        if m.from_user.id != ADMIN_ID:
            return
        username = user_steps[sid]["username"]
        password = user_steps[sid]["password"]
        expiry = txt
        ok, result = create_user_api(username, password, expiry)
        user_steps.pop(sid, None)
        return bot.send_message(m.chat.id, format_create_response(result, username, password, expiry), reply_markup=back_menu())

    if step == "delete_username":
        if m.from_user.id != ADMIN_ID:
            return
        ok, result = delete_user_api(txt)
        user_steps.pop(sid, None)
        return bot.send_message(m.chat.id, f"🗑 <b>DELETE RESULT</b>\n\n<code>{esc(result)}</code>", reply_markup=back_menu())

print("✅ Bot running...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
