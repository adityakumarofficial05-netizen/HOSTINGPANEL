import traceback
import os, sys, ast, json, uuid, zipfile, shutil, sqlite3, subprocess, urllib.request, threading, time, base64
from pathlib import Path
from datetime import datetime, date, timedelta
from flask import Flask, request, redirect, url_for, session, send_file, jsonify, render_template_string

APP_SECRET=os.getenv("APP_SECRET","change-this-secret")
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","ADITYA")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","ADITYA123")
ADMIN_API_KEY=os.getenv("ADMIN_API_KEY","NEXA")
FIREBASE_DATABASE_URL=os.getenv("FIREBASE_DATABASE_URL","https://deathmods8088-default-rtdb.firebaseio.com").rstrip("/")
FIREBASE_ENABLED=os.getenv("FIREBASE_ENABLED","1")=="1"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROJECT_DIR = DATA_DIR / "projects"
DB_PATH = DATA_DIR / "hosting.db"

DATA_DIR.mkdir(exist_ok=True)
PROJECT_DIR.mkdir(exist_ok=True)

app=Flask(__name__)
app.secret_key=APP_SECRET
processes={}
WATCHDOG_STARTED=False

CSS="""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
*{box-sizing:border-box}body{margin:0;min-height:100vh;font-family:Inter,Arial;color:#eef4ff;background:radial-gradient(circle at 15% 5%,rgba(56,189,248,.22),transparent 28%),radial-gradient(circle at 80% 15%,rgba(139,92,246,.26),transparent 28%),linear-gradient(135deg,#020617,#070b1d 55%,#050714)}.wrap{max-width:1240px;margin:auto;padding:18px}.appgrid{display:grid;grid-template-columns:260px 1fr;gap:18px}.sidebar{position:sticky;top:18px;align-self:start;min-height:calc(100vh - 36px);background:linear-gradient(180deg,rgba(15,23,42,.92),rgba(2,6,23,.92));border:1px solid rgba(255,255,255,.1);border-radius:30px;padding:18px;box-shadow:0 25px 90px #0007}.logoBox{display:flex;align-items:center;gap:12px;padding:12px;border-radius:22px;background:linear-gradient(135deg,rgba(56,189,248,.15),rgba(139,92,246,.15));border:1px solid rgba(255,255,255,.08)}.logo{width:48px;height:48px;border-radius:18px;display:grid;place-items:center;font-size:24px;background:linear-gradient(135deg,#38bdf8,#8b5cf6,#ec4899)}.nav{display:grid;gap:10px;margin-top:18px}.nav a{padding:13px 14px;border-radius:18px;background:rgba(255,255,255,.04);color:#dbeafe;font-weight:800;text-decoration:none}.topbar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;padding:18px 22px;border-radius:28px;background:linear-gradient(135deg,rgba(15,23,42,.88),rgba(2,6,23,.72));border:1px solid rgba(255,255,255,.1)}.card{background:linear-gradient(145deg,rgba(15,23,42,.88),rgba(2,6,23,.88));border:1px solid rgba(255,255,255,.1);border-radius:28px;padding:22px;margin:16px 0;box-shadow:0 18px 70px #0006;overflow:hidden}.login{max-width:500px;margin:8vh auto}.bigIcon{width:76px;height:76px;border-radius:28px;display:grid;place-items:center;font-size:38px;margin-bottom:16px;background:linear-gradient(135deg,#38bdf8,#8b5cf6,#ec4899)}h1{margin:0 0 8px;font-size:clamp(30px,5vw,46px);font-weight:900;letter-spacing:-1.2px}h2{margin:0 0 12px;font-size:22px;font-weight:900}.muted{color:#8ea0c2}a{text-decoration:none;color:inherit}.btn,button{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:0;border-radius:16px;padding:12px 16px;margin:5px;background:linear-gradient(135deg,#8b5cf6,#38bdf8);color:white;font-weight:900;cursor:pointer}.ok{background:linear-gradient(135deg,#22c55e,#06b6d4)}.danger{background:linear-gradient(135deg,#ef4444,#f97316)}.pink{background:linear-gradient(135deg,#ec4899,#8b5cf6)}.dark{background:rgba(255,255,255,.08)}input{width:calc(100% - 10px);padding:14px 15px;margin:6px 5px;border-radius:16px;border:1px solid rgba(148,163,184,.2);background:rgba(2,6,23,.7);color:#fff;font-weight:700}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:16px 0}.stat{border-radius:24px;padding:20px;background:linear-gradient(145deg,rgba(17,24,39,.86),rgba(2,6,23,.76));border:1px solid rgba(255,255,255,.1)}.stat b{display:block;font-size:36px}.stat p{margin:6px 0 0;color:#8ea0c2;font-weight:800}.tableWrap{overflow:auto;border-radius:22px}table{width:100%;border-collapse:separate;border-spacing:0 10px}th{color:#9fb0d0;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.8px;padding:10px 14px}td{padding:14px;background:rgba(2,6,23,.56)}.badge{display:inline-flex;padding:8px 12px;border-radius:999px;font-size:12px;font-weight:900;background:rgba(56,189,248,.13);border:1px solid rgba(56,189,248,.28);color:#c8f7ff}pre{white-space:pre-wrap;background:rgba(2,6,23,.75);border:1px solid rgba(148,163,184,.16);border-radius:18px;padding:16px;overflow:auto;color:#dbeafe}.actions{display:flex;flex-wrap:wrap;gap:5px}.split{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:900px){.appgrid{grid-template-columns:1fr}.sidebar{position:relative;min-height:auto;top:0}.stats{grid-template-columns:repeat(2,1fr)}.split{grid-template-columns:1fr}}@media(max-width:650px){.wrap{padding:12px}.card,.topbar,.sidebar{border-radius:22px;padding:16px}table,tbody,tr,td,th{display:block}th{display:none}td{border-radius:14px!important;margin:6px 0}.actions .btn{width:100%;margin:3px 0}}
</style>
"""
BASE_HTML="<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>BotHost Firebase 24/7</title>"+CSS+"</head><body><div class='wrap'>{{body|safe}}</div></body></html>"
PACKAGE_MAP={"telebot":"pyTelegramBotAPI","PIL":"pillow","cv2":"opencv-python","Crypto":"pycryptodome","bs4":"beautifulsoup4","yaml":"pyyaml","dotenv":"python-dotenv","telegram":"python-telegram-bot","requests":"requests","aiohttp":"aiohttp","flask":"flask","numpy":"numpy","pandas":"pandas","jwt":"PyJWT","dns":"dnspython","pymongo":"pymongo","redis":"redis","qrcode":"qrcode","colorama":"colorama"}

def page(body): return render_template_string(BASE_HTML, body=body)
def fburl(path): return f"{FIREBASE_DATABASE_URL}/{path.strip('/')}.json"
def firebase_put(path,data):
    if not FIREBASE_ENABLED: return False
    try:
        urllib.request.urlopen(urllib.request.Request(fburl(path),data=json.dumps(data).encode(),headers={"Content-Type":"application/json"},method="PUT"),timeout=12).read(); return True
    except Exception as e: print("firebase_put_error",e); return False
def firebase_patch(path,data):
    if not FIREBASE_ENABLED: return False
    try:
        urllib.request.urlopen(urllib.request.Request(fburl(path),data=json.dumps(data).encode(),headers={"Content-Type":"application/json"},method="PATCH"),timeout=12).read(); return True
    except Exception as e: print("firebase_patch_error",e); return False
def firebase_get(path):
    if not FIREBASE_ENABLED: return None
    try: return json.loads(urllib.request.urlopen(fburl(path),timeout=12).read().decode() or "null")
    except Exception as e: print("firebase_get_error",e); return None
def firebase_delete(path):
    if not FIREBASE_ENABLED: return False
    try: urllib.request.urlopen(urllib.request.Request(fburl(path),method="DELETE"),timeout=12).read(); return True
    except Exception: return False
def b64file(path): return base64.b64encode(Path(path).read_bytes()).decode()
def writeb64(data,path): Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_bytes(base64.b64decode(data.encode()))

def db():
    con = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    con.row_factory = sqlite3.Row

    con.execute("PRAGMA journal_mode=WAL")

    con.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        expiry_date TEXT,
        created_at TEXT
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS projects(
        id TEXT PRIMARY KEY,
        username TEXT,
        name TEXT,
        path TEXT,
        main_file TEXT,
        status TEXT DEFAULT 'stopped',
        autostart INTEGER DEFAULT 1,
        created_at TEXT
    )
    """)

    return con

def find_main(folder):
    for name in ["main.py","bot.py","app.py","index.py"]:
        p=folder/name
        if p.exists(): return p
    files=list(folder.rglob("*.py")); return files[0] if files else None

def sync_users_from_firebase():
    data=firebase_get("hosting/users") or {}
    if not isinstance(data,dict): return
    con=db()
    for username,u in data.items():
        if isinstance(u,dict):
            con.execute("INSERT OR REPLACE INTO users(username,password,expiry_date,created_at) VALUES(?,?,?,?)",(u.get("username",username),u.get("password",""),u.get("expiry_date","2099-12-31"),u.get("created_at",datetime.now().isoformat(timespec="seconds"))))
    con.commit()
def sync_projects_from_firebase():
    data=firebase_get("hosting/projects") or {}
    if not isinstance(data,dict): return
    con=db()
    for pid,p in data.items():
        if not isinstance(p,dict): continue
        username=p.get("username","ADMIN"); name=p.get("name","bot.py"); folder=PROJECT_DIR/username/pid
        main_path=folder/p.get("main_name","bot.py")
        if p.get("file_b64") and not main_path.exists(): writeb64(p["file_b64"],main_path)
        elif p.get("zip_b64") and not folder.exists():
            zp=DATA_DIR/f"{pid}_restore.zip"; writeb64(p["zip_b64"],zp); folder.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(zp) as z: z.extractall(folder)
            zp.unlink(missing_ok=True); found=find_main(folder)
            if found: main_path=found
        if main_path.exists():
            con.execute("INSERT OR REPLACE INTO projects(id,username,name,path,main_file,status,autostart,created_at) VALUES(?,?,?,?,?,?,?,?)",(pid,username,name,str(folder),str(main_path),p.get("status","stopped"),int(p.get("autostart",1)),p.get("created_at",datetime.now().isoformat(timespec="seconds"))))
    con.commit()

def current_user(): return session.get("username")
def is_admin(): return session.get("role")=="admin"
def login_required(fn):
    def wrapper(*a,**kw):
        if not current_user(): return redirect(url_for("login"))
        return fn(*a,**kw)
    wrapper.__name__=fn.__name__; return wrapper
def expired(exp):
    try: return date.today()>datetime.strptime(exp,"%Y-%m-%d").date()
    except Exception: return True
def owner_ok(row): return is_admin() or row["username"]==current_user()

def imports_from_file(pyfile):
    mods=set()
    try:
        tree=ast.parse(pyfile.read_text(encoding="utf-8",errors="ignore"))
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):
                for a in n.names: mods.add(a.name.split(".")[0])
            if isinstance(n,ast.ImportFrom) and n.module: mods.add(n.module.split(".")[0])
    except Exception: pass
    return mods
def auto_install(pyfile,logfile):
    skip={"os","sys","json","time","datetime","sqlite3","subprocess","threading","asyncio","random","math","pathlib","re","zipfile","shutil","uuid","logging","base64","hashlib","typing","collections","urllib","email","html","csv"}
    with open(logfile,"a",encoding="utf-8") as log:
        log.write("\n[HOST] Auto install checking...\n")
        for m in sorted(imports_from_file(pyfile)):
            if m in skip or (hasattr(sys,"stdlib_module_names") and m in sys.stdlib_module_names): continue
            try: __import__(m)
            except ModuleNotFoundError:
                pkg=PACKAGE_MAP.get(m,m); log.write(f"[AUTO-INSTALL] pip install {pkg}\n"); log.flush()
                subprocess.run([sys.executable,"-m","pip","install",pkg],stdout=log,stderr=log,timeout=300)
            except Exception: pass
        log.write("[HOST] Auto install done.\n")

def save_project(file, username):
    pid = str(uuid.uuid4())[:8]
    folder = PROJECT_DIR / username / pid
    folder.mkdir(parents=True, exist_ok=True)

    name = (file.filename or "bot.py").replace("/", "_").replace("\\", "_")
    saved = folder / name
    file.save(saved)

    data = {
        "id": pid,
        "username": username,
        "name": name,
        "status": "stopped",
        "autostart": 1,
        "created_at": datetime.now().isoformat(timespec="seconds")
    }

    main = None

    if name.lower().endswith(".zip"):
        data["zip_b64"] = b64file(saved)

        with zipfile.ZipFile(saved) as z:
            z.extractall(folder)

        saved.unlink(missing_ok=True)

        # requirements skip (Render safe)
        req = folder / "requirements.txt"
        if req.exists():
            print("requirements.txt found but ignored (Render safe mode)")

        main = find_main(folder)

    elif name.lower().endswith(".py"):
        main = saved
        data["file_b64"] = b64file(saved)

    else:
        raise ValueError("Only .py or .zip allowed")

    if not main:
        raise ValueError("No Python file found")

    data["main_name"] = main.name

    # ❌ REMOVED auto_install (this was crashing Render)
    # auto_install(main, folder/"host.log")

    con = db()
    con.execute(
        "INSERT INTO projects(id,username,name,path,main_file,status,autostart,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (pid, username, name, str(folder), str(main), "stopped", 1, data["created_at"])
    )
    con.commit()

    firebase_put(f"hosting/projects/{pid}", data)
    return pid


def get_project(pid):
    return db().execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()


def restore_project_if_missing(row):
    if Path(row["main_file"]).exists():
        return True

    sync_projects_from_firebase()
    row2 = get_project(row["id"])

    return bool(row2 and Path(row2["main_file"]).exists())
def run_project(row):
    pid=row["id"]
    if not restore_project_if_missing(row): return
    row=get_project(pid); folder=Path(row["path"]); main=Path(row["main_file"]); logf=folder/"host.log"
    if pid in processes and processes[pid].poll() is None: return
    auto_install(main,logf)
    with open(logf,"a",encoding="utf-8") as log:
        log.write(f"\n[HOST] Starting {main.name} at {datetime.now()}\n")
        processes[pid]=subprocess.Popen([sys.executable,str(main)],cwd=str(folder),stdout=log,stderr=log,stdin=subprocess.DEVNULL)
    con=db(); con.execute("UPDATE projects SET status='running', autostart=1 WHERE id=?",(pid,)); con.commit()
    firebase_patch(f"hosting/projects/{pid}",{"status":"running","autostart":1})
def stop_project(row,manual=True):
    pid=row["id"]; p=processes.get(pid)
    if p and p.poll() is None:
        p.terminate()
        try: p.wait(8)
        except Exception: p.kill()
    con=db()
    if manual:
        con.execute("UPDATE projects SET status='stopped', autostart=0 WHERE id=?",(pid,)); firebase_patch(f"hosting/projects/{pid}",{"status":"stopped","autostart":0})
    else:
        con.execute("UPDATE projects SET status='stopped' WHERE id=?",(pid,)); firebase_patch(f"hosting/projects/{pid}",{"status":"stopped"})
    con.commit()

def watchdog_loop():
    time.sleep(4)
    while True:
        try:
            sync_users_from_firebase(); sync_projects_from_firebase()
            for row in db().execute("SELECT * FROM projects WHERE autostart=1").fetchall():
                proc=processes.get(row["id"])
                if not proc or proc.poll() is not None:
                    folder=Path(row["path"]); folder.mkdir(parents=True,exist_ok=True)
                    with open(folder/"host.log","a",encoding="utf-8") as log: log.write(f"\n[WATCHDOG] Auto restart at {datetime.now()}\n")
                    run_project(row)
        except Exception as e: print("watchdog_error",e)
        time.sleep(20)
def start_watchdog():
    global WATCHDOG_STARTED
    if not WATCHDOG_STARTED:
        WATCHDOG_STARTED=True; threading.Thread(target=watchdog_loop,daemon=True).start()
start_watchdog()

@app.route("/health")
@app.route("/keepalive")
def health(): return jsonify({"ok":True,"message":"Firebase persistent 24/7 watchdog awake","time":datetime.now().isoformat()})
@app.route("/api")
def api():
    if not current_user() or not is_admin(): return jsonify({"status":False,"message":"Private API. Admin login required."}),403
    base=request.host_url.rstrip("/")
    return page(f"<div class='card login'><div class='bigIcon'>🔒</div><h1>Private API</h1><pre>{base}/api/create-username=example=password=809808?key=NEXA&date=2026-12-31</pre><pre>{base}/api/users?key=NEXA</pre><pre>{base}/api/delete-user=example?key=NEXA</pre><a class='btn' href='/dashboard'>Dashboard</a></div>")
@app.route("/api/create-username=<username>=password=<password>")
def api_create(username,password):
    if request.args.get("key")!=ADMIN_API_KEY: return jsonify({"status":False,"message":"Unauthorized Access"}),403
    exp=request.args.get("date") or request.args.get("expiry_date") or (date.today()+timedelta(days=30)).isoformat(); created=datetime.now().isoformat(timespec="seconds")
    con=db(); con.execute("INSERT OR REPLACE INTO users(username,password,expiry_date,created_at) VALUES(?,?,?,?)",(username,password,exp,created)); con.commit()
    firebase_put(f"hosting/users/{username}",{"username":username,"password":password,"expiry_date":exp,"created_at":created})
    return jsonify({"status":True,"ok":True,"message":"User created","username":username,"password":password,"expiry_date":exp})
@app.route("/api/users")
@app.route("/api/list-users")
def api_users():
    if request.args.get("key")!=ADMIN_API_KEY: return jsonify({"status":False,"message":"Unauthorized Access"}),403
    sync_users_from_firebase()
    users=[dict(r) for r in db().execute("SELECT username,password,expiry_date,created_at FROM users ORDER BY id DESC").fetchall()]
    return jsonify({"status":True,"count":len(users),"users":users})
@app.route("/api/delete-user=<username>")
def api_delete_user(username):
    if request.args.get("key")!=ADMIN_API_KEY: return jsonify({"status":False,"message":"Unauthorized Access"}),403
    delete_user_data(username); return jsonify({"status":True,"message":"User deleted","username":username})

@app.route("/")
def home(): return redirect(url_for("dashboard" if current_user() else "login"))
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        sync_users_from_firebase()
        u=request.form.get("username","").strip()
        p=request.form.get("password","").strip()

        print("LOGIN ATTEMPT:", u)

        if u==ADMIN_USERNAME and p==ADMIN_PASSWORD:
            print("ADMIN LOGIN SUCCESS")
            session.clear()
            session["username"]=u
            session["role"]="admin"
            return redirect(url_for("dashboard"))

        row=db().execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone()

        print("DB ROW:", row)

        if row:
            print("EXPIRY DATE:", row["expiry_date"])

        if row and not expired(row["expiry_date"]):
            print("USER LOGIN SUCCESS")
            session.clear()
            session["username"]=u
            session["role"]="user"
            return redirect(url_for("dashboard"))

        print("LOGIN FAILED")
    return page("<div class='card login'><div class='bigIcon'>🔥</div><h1>Bot Hosting 24/7</h1><p class='muted'>Firebase saved users + one-time upload backup + watchdog restart.</p><form method='post'><input name='username' placeholder='👤 Username' required><input name='password' type='password' placeholder='🔒 Password' required><button>⚡ Login Panel</button></form><a class='btn pink' href='http://t.me/@DI_HOSTING_BOT'>💬 DM TO BUY</a></div>")
@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    sync_users_from_firebase(); sync_projects_from_firebase()
    con=db(); projects=con.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall() if is_admin() else con.execute("SELECT * FROM projects WHERE username=? ORDER BY created_at DESC",(current_user(),)).fetchall(); users=con.execute("SELECT * FROM users ORDER BY id DESC").fetchall() if is_admin() else []
    running=len([p for p in projects if p["status"]=="running"]); total=len(projects); stopped=total-running
    rows="".join([f"<tr><td>{p['name']}<br><span class='muted'>{p['id']}</span></td><td>{p['username']}</td><td><span class='badge'>{p['status']} • 24/7:{p['autostart']}</span></td><td><div class='actions'><a class='btn ok' href='/project/{p['id']}/start'>▶ Start</a><a class='btn danger' href='/project/{p['id']}/stop'>■ Stop</a><a class='btn' href='/project/{p['id']}/restart'>↻ Restart</a><a class='btn ok' href='/project/{p['id']}/autostart-on'>♾ 24/7 ON</a><a class='btn danger' href='/project/{p['id']}/autostart-off'>♾ OFF</a><a class='btn' href='/project/{p['id']}/logs'>📜 Logs</a><a class='btn' href='/project/{p['id']}/download'>⬇ Download</a><a class='btn danger' href='/project/{p['id']}/delete'>🗑 Delete</a></div></td></tr>" for p in projects])
    admin=""
    if is_admin():
        user_rows="".join([f"<tr><td>{u['username']}</td><td>{u['expiry_date']}</td><td><a class='btn danger' href='/admin/delete-user/{u['username']}'>Delete</a></td></tr>" for u in users])
        admin=f"<div class='split'><div class='card'><h2>👑 User Creator</h2><form method='post' action='/admin/create-user'><input name='username' placeholder='👤 Username' required><input name='password' placeholder='🔒 Password' required><input name='expiry_date' type='date' required><button>✨ Create User</button></form></div><div class='card'><h2>🔒 Private API</h2><pre>{request.host_url.rstrip('/')}/api/create-username=example=password=809808?key=NEXA&date=2026-12-31</pre><pre>{request.host_url.rstrip('/')}/api/users?key=NEXA</pre><pre>{request.host_url.rstrip('/')}/keepalive</pre></div></div><div class='card'><h2>👥 Firebase Users List</h2><div class='tableWrap'><table><tr><th>Username</th><th>Expiry</th><th>Action</th></tr>{user_rows}</table></div></div>"
    return page(f"<div class='appgrid'><aside class='sidebar'><div class='logoBox'><div class='logo'>🔥</div><div><b>BotHost Firebase</b><br><span class='muted'>{session.get('role').upper()}</span></div></div><div class='nav'><a href='/dashboard'>🏠 Dashboard</a><a href='/keepalive'>♾ KeepAlive</a><a href='http://t.me/PAIDHOSTING_BOT'>💬 DM TO BUY</a><a href='/logout'>🚪 Logout</a></div></aside><main><div class='topbar'><div><h1>Firebase 24/7 Dashboard</h1><p class='muted'>Users and uploaded bot source are saved in Firebase.</p></div><a class='btn danger' href='/logout'>🚪 Logout</a></div><div class='stats'><div class='stat'><b>{total}</b><p>📦 Total Files</p></div><div class='stat'><b>{running}</b><p>🟢 Running</p></div><div class='stat'><b>{stopped}</b><p>⏹ Stopped</p></div><div class='stat'><b>{len(users)}</b><p>👥 Users</p></div></div><div class='card'><h2>⬆ One-Time Upload</h2><p class='muted'>Upload once. Source backed up to Firebase. Watchdog restores and runs after restart.</p><form method='post' action='/upload' enctype='multipart/form-data'><input type='file' name='file' accept='.py,.zip' required><button>🚀 Upload & Backup</button></form></div>{admin}<div class='card'><h2>🧩 Hosted Projects</h2><div class='tableWrap'><table><tr><th>File</th><th>Owner</th><th>Status</th><th>Action</th></tr>{rows}</table></div></div></main></div>")

@app.route("/admin/create-user",methods=["POST"])
@login_required
def create_user():
    if not is_admin(): return "Forbidden",403
    u=request.form["username"].strip(); p=request.form["password"].strip(); exp=request.form["expiry_date"].strip(); created=datetime.now().isoformat(timespec="seconds")
    con=db(); con.execute("INSERT OR REPLACE INTO users(username,password,expiry_date,created_at) VALUES(?,?,?,?)",(u,p,exp,created)); con.commit()
    firebase_put(f"hosting/users/{u}",{"username":u,"password":p,"expiry_date":exp,"created_at":created}); return redirect(url_for("dashboard"))
def delete_user_data(username):
    con=db()
    for p in con.execute("SELECT * FROM projects WHERE username=?",(username,)).fetchall():
        stop_project(p,manual=True); shutil.rmtree(p["path"],ignore_errors=True); firebase_delete(f"hosting/projects/{p['id']}")
    con.execute("DELETE FROM projects WHERE username=?",(username,)); con.execute("DELETE FROM users WHERE username=?",(username,)); con.commit(); firebase_delete(f"hosting/users/{username}")
@app.route("/admin/delete-user/<username>")
@login_required
def delete_user(username):
    if not is_admin(): return "Forbidden",403
    delete_user_data(username); return redirect(url_for("dashboard"))
@app.route("/upload",methods=["POST"])
@login_required

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    try:
        f = request.files.get("file")

        if not f:
            return redirect(url_for("dashboard"))

        print("UPLOAD STARTED:", f.filename)

        save_project(f, current_user())

        print("UPLOAD SUCCESS")

        return redirect(url_for("dashboard"))

    except Exception as e:
        print("UPLOAD ERROR:", e)
        traceback.print_exc()
        return redirect(url_for("dashboard"))


@app.route("/project/<pid>/stop")
@login_required
def stop(pid):
    r = get_project(pid)
    if r and owner_ok(r):
        stop_project(r, manual=True)
    return redirect(url_for("dashboard"))


@app.route("/project/<pid>/restart")
@login_required
def restart(pid):
    r = get_project(pid)
    if r and owner_ok(r):
        stop_project(r, manual=False)
        run_project(r)
    return redirect(url_for("dashboard"))
def autostart_on(pid):
    r=get_project(pid)
    if r and owner_ok(r):
        con=db(); con.execute("UPDATE projects SET autostart=1 WHERE id=?",(pid,)); con.commit(); firebase_patch(f"hosting/projects/{pid}",{"autostart":1}); run_project(r)
    return redirect(url_for("dashboard"))
@app.route("/project/<pid>/autostart-off")
@login_required
def autostart_off(pid):
    r=get_project(pid)
    if r and owner_ok(r):
        con=db(); con.execute("UPDATE projects SET autostart=0 WHERE id=?",(pid,)); con.commit(); firebase_patch(f"hosting/projects/{pid}",{"autostart":0})
    return redirect(url_for("dashboard"))
@app.route("/project/<pid>/logs")
@login_required
def logs(pid):
    r=get_project(pid)
    if not r or not owner_ok(r): return "Not found",404
    lf=Path(r["path"])/"host.log"; txt=lf.read_text(encoding="utf-8",errors="ignore") if lf.exists() else "No logs"
    return page(f"<div class='card'><h1>📜 Logs</h1><pre>{txt}</pre><a class='btn' href='/dashboard'>Back</a></div>")
@app.route("/project/<pid>/download")
@login_required
def download(pid):
    r=get_project(pid)
    if not r or not owner_ok(r): return "Not found",404
    if not restore_project_if_missing(r): return "File not found",404
    r=get_project(pid); zp=DATA_DIR/f"{pid}.zip"; shutil.make_archive(str(zp).replace(".zip",""),"zip",r["path"])
    return send_file(zp,as_attachment=True)
@app.route("/project/<pid>/delete")
@login_required
def delete(pid):
    r=get_project(pid)
    if r and owner_ok(r):
        stop_project(r,manual=True); shutil.rmtree(r["path"],ignore_errors=True)
        con=db(); con.execute("DELETE FROM projects WHERE id=?",(pid,)); con.commit(); firebase_delete(f"hosting/projects/{pid}")
    return redirect(url_for("dashboard"))

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")),debug=False)
