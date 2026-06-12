import sqlite3
from config import DATABASE, ADMIN_TELEGRAM_ID

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                auth_method TEXT NOT NULL,
                google_email TEXT,
                phone_number TEXT,
                credits INTEGER DEFAULT 5,
                is_banned INTEGER DEFAULT 0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS email_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS inbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_email TEXT NOT NULL,
                sender TEXT NOT NULL,
                subject TEXT,
                body TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS admin_config (
                admin_telegram_id INTEGER UNIQUE NOT NULL
            );
        ''')
        conn.execute("INSERT OR IGNORE INTO admin_config (admin_telegram_id) VALUES (?)", (ADMIN_TELEGRAM_ID,))