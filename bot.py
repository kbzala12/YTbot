# -*- coding: utf-8 -*-
"""
Telegram Reward & Submission Bot (Production-ready)
Author: You
Lib: pyTelegramBotAPI (telebot)

Features:
- /start with referral (deep-link)
- Daily bonus (IST day-based)
- Coins wallet (profile, admin coin ops)
- URL submission (YouTube validation + coin cost)
- Admin tools: stats, submissions (paginated), add/remove/set coins, broadcast, export CSV
- Anti-flood + simple abuse protections
- Robust sqlite with WAL, indices, context managers
"""

import os
import re
import csv
import time
import sqlite3
import datetime as dt
from zoneinfo import ZoneInfo
from typing import Optional, Tuple

import telebot
from telebot import types

# ---------------- CONFIG ----------------
# Use environment variables for secrets; fallback to placeholders for local testing
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBotUsername")  # without @
WEB_URL = os.getenv("WEB_URL", "https://yourwebapp.com")

REF_BONUS = int(os.getenv("REF_BONUS", "100"))
DAILY_BONUS = int(os.getenv("DAILY_BONUS", "10"))
SUBMIT_COST = int(os.getenv("SUBMIT_COST", "1280"))

TZ = ZoneInfo("Asia/Kolkata")  # Project timezone
DB_PATH = os.getenv("DB_PATH", "bot.db")

# Anti-flood tuning
GLOBAL_RATE_LIMIT_SEC = 0.8
CMD_COOLDOWNS_SEC = {
    "daily": 5.0,
    "submit": 2.0,
}

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# In-memory flood control
_last_seen_global = 0.0
_last_cmd_ts = {}  # {(user_id, "cmd"): ts}

# ---------------- DB LAYER ----------------
def db_connect():
    conn = sqlite3.connect(DB_PATH, timeout=15, isolation_level=None)  # autocommit
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                coins INTEGER NOT NULL DEFAULT 0,
                last_bonus TEXT,
                referrer INTEGER,
                created_at TEXT NOT NULL
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS submissions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
        """)
        # helpful indices
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_referrer ON users(referrer);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_sub_user ON submissions(user_id);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_sub_time ON submissions(time);")

init_db()

# ---------------- HELPERS ----------------
YT_REGEX = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[A-Za-z0-9_\-]{6,}$",
    re.IGNORECASE
)

def now_ist():
    return dt.datetime.now(TZ)

def today_ist_str():
    return now_ist().date().isoformat()

def is_youtube_url(url: str) -> bool:
    return bool(YT_REGEX.match(url.strip()))

def ensure_user(user_id: int, referrer: Optional[int] = None) -> Tuple[bool, Optional[int]]:
    """
    Returns (created, effective_referrer)
    - Only sets referrer if user is new, valid, and not self.
    - Awards referral bonus only on first creation.
    """
    created = False
    effective_ref = None
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, referrer FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if row:
            return created, row[1]
        # new user
        if referrer == user_id:
            referrer = None
        # check referrer exists
        if referrer:
            c.execute("SELECT 1 FROM users WHERE user_id=?", (referrer,))
            if not c.fetchone():
                referrer = None
        c.execute(
            "INSERT INTO users(user_id, coins, last_bonus, referrer, created_at) VALUES (?,?,?,?,?)",
            (user_id, 0, None, referrer, now_ist().isoformat())
        )
        created = True
        effective_ref = referrer
    return created, effective_ref

def get_coins(user_id: int) -> int:
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        return row[0] if row else 0

def update_coins(user_id: int, delta: int):
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (delta, user_id))

def set_coins(user_id: int, value: int):
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET coins = ? WHERE user_id=?", (value, user_id))

def get_last_bonus(user_id: int) -> Optional[str]:
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT last_bonus FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        return row[0] if row and row[0] else None

def set_last_bonus_today(user_id: int):
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET last_bonus=? WHERE user_id=?", (today_ist_str(), user_id))

def add_submission(user_id: int, url: str):
    with db_connect() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO submissions(user_id, url, time, status) VALUES (?,?,?,?)",
            (user_id, url, now_ist().isoformat(), "pending")
        )

def get_submissions(limit=10, offset=0):
    with db_connect() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, user_id, url, time, status FROM submissions ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return c.fetchall()

def count_submissions():
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(1) FROM submissions")
        return c.fetchone()[0]

def get_stats():
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(1) FROM users")
        total_users = c.fetchone()[0]
        c.execute("SELECT COUNT(1) FROM submissions")
        total_subs = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(coins),0) FROM users")
        total_coins = c.fetchone()[0]
        return total_users, total_subs, total_coins

# ---------------- ANTI-FLOOD ----------------
def global_rate_limit():
    global _last_seen_global
    now = time.time()
    if now - _last_seen_global < GLOBAL_RATE_LIMIT_SEC:
        time.sleep(GLOBAL_RATE_LIMIT_SEC - (now - _last_seen_global))
    _last_seen_global = time.time()

def cmd_cooldown(user_id: int, key: str, cooldown: float) -> bool:
    """
    Returns True if allowed, False if still cooling down.
    """
    now = time.time()
    k = (user_id, key)
    ts = _last_cmd_ts.get(k, 0)
    if now - ts < cooldown:
        return False
    _last_cmd_ts[k] = now
    return True

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ---------------- UI BUILDERS ----------------
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌐 Web Open", "👥 Invite")
    kb.add("🎁 Daily Bonus", "👤 Profile")
    kb.add("📤 Submit URL")
    return kb

# ---------------- COMMANDS ----------------
@bot.message_handler(commands=['start'])
def start(message: types.Message):
    global_rate_limit()
    # parse deep-link referrer
    referrer = None
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) > 1:
        try:
            referrer = int(parts[1])
        except:
            referrer = None

    created, effective_ref = ensure_user(message.chat.id, referrer)

    # award referrer only once for new user
    if created and effective_ref and effective_ref != message.chat.id:
        update_coins(effective_ref, REF_BONUS)
        try:
            bot.send_message(effective_ref, f"🎉 आपको <b>{REF_BONUS}</b> कॉइन्स मिले! आपके invite से नया यूज़र जुड़ा।")
        except:
            pass

    bot.send_message(
        message.chat.id,
        "👋 स्वागत है!\nनीचे मेन्यू से अपना काम चुनें:",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message: types.Message):
    global_rate_limit()
    text = (
        "<b>कमांड्स:</b>\n"
        "/help – मदद\n"
        "/submissions [page] – (Admin) Recent submissions\n"
        "/stats – (Admin) कुल यूज़र्स/सबमिशन्स/कॉइन्स\n"
        "/addcoins <id> <amount> – (Admin) कॉइन्स जोड़ें\n"
        "/removecoins <id> <amount> – (Admin) कॉइन्स घटाएँ\n"
        "/setcoins <id> <value> – (Admin) कॉइन्स सेट करें\n"
        "/broadcast <text> – (Admin) सभी यूज़र्स को मैसेज\n"
        "/export – (Admin) submissions.csv एक्सपोर्ट\n"
    )
    bot.send_message(message.chat.id, text)

# ---------------- BUTTONS ----------------
@bot.message_handler(func=lambda m: m.text == "🌐 Web Open")
def web_open(message: types.Message):
    global_rate_limit()
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔗 WebApp खोलें", url=WEB_URL)
    markup.add(btn)
    bot.send_message(message.chat.id, "👉 WebApp खोलने के लिए नीचे क्लिक करें:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👥 Invite")
def invite(message: types.Message):
    global_rate_limit()
    link = f"https://t.me/{BOT_USERNAME}?start={message.chat.id}"
    bot.send_message(
        message.chat.id,
        f"🔗 अपनी Invite Link:\n<code>{link}</code>\n\nहर नए यूज़र पर आपको <b>{REF_BONUS}</b> कॉइन्स मिलेंगे।"
    )

@bot.message_handler(func=lambda m: m.text == "🎁 Daily Bonus")
def daily_bonus(message: types.Message):
    global_rate_limit()
    if not cmd_cooldown(message.chat.id, "daily", CMD_COOLDOWNS_SEC["daily"]):
        return bot.send_message(message.chat.id, "⏳ थोड़ा इंतज़ार करें, फिर से ट्राय करें।")

    last = get_last_bonus(message.chat.id)
    today = today_ist_str()
    if last == today:
        return bot.send_message(message.chat.id, "⏳ आज का Daily Bonus पहले ही ले लिया है।")
    update_coins(message.chat.id, DAILY_BONUS)
    set_last_bonus_today(message.chat.id)
    bot.send_message(message.chat.id, f"🎉 आपको <b>{DAILY_BONUS}</b> कॉइन्स मिले!")

@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(message: types.Message):
    global_rate_limit()
    coins = get_coins(message.chat.id)
    bot.send_message(message.chat.id, f"👤 <b>प्रोफ़ाइल</b>\n\n💰 Coins: <b>{coins}</b>")

@bot.message_handler(func=lambda m: m.text == "📤 Submit URL")
def submit_url(message: types.Message):
    global_rate_limit()
    coins = get_coins(message.chat.id)
    if coins < SUBMIT_COST:
        return bot.send_message(message.chat.id, f"❌ आपके पास पर्याप्त Coins नहीं हैं। (कम से कम {SUBMIT_COST})")
    msg = bot.send_message(message.chat.id, "📥 अपना YouTube URL भेजें:")
    bot.register_next_step_handler(msg, process_url)

def process_url(message: types.Message):
    global_rate_limit()
    user_id = message.chat.id
    url = message.text.strip()

    if not cmd_cooldown(user_id, "submit", CMD_COOLDOWNS_SEC["submit"]):
        return bot.send_message(user_id, "⏳ थोड़ा इंतज़ार करें, फिर से ट्राय करें।")

    if not is_youtube_url(url):
        return bot.send_message(user_id, "❌ वैध YouTube URL भेजें (youtube.com/watch?v=... या youtu.be/...)")

    coins = get_coins(user_id)
    if coins < SUBMIT_COST:
        return bot.send_message(user_id, "❌ Coins कम हैं।")

    # deduct and store
    update_coins(user_id, -SUBMIT_COST)
    add_submission(user_id, url)

    bot.send_message(user_id, "✅ आपका URL सफलतापूर्वक सबमिट हो गया।")
    try:
        bot.send_message(ADMIN_ID, f"📩 नया सबमिशन:\n👤 User: <code>{user_id}</code>\n🔗 URL: {url}")
    except:
        pass

# ---------------- ADMIN ----------------
@bot.message_handler(commands=['submissions'])
def admin_submissions(message: types.Message):
    global_rate_limit()
    if not is_admin(message.chat.id):
        return
    # pagination: /submissions [page]
    try:
        parts = message.text.strip().split()
        page = int(parts[1]) if len(parts) > 1 else 1
        page = max(page, 1)
    except:
        page = 1

    per_page = 10
    offset = (page - 1) * per_page
    rows = get_submissions(limit=per_page, offset=offset)
    total = count_submissions()
    pages = max(1, (total + per_page - 1) // per_page)

    if not rows:
        return bot.send_message(ADMIN_ID, "📭 अभी तक कोई सबमिशन नहीं।")

    text = [f"📋 <b>Recent Submissions</b> (Page {page}/{pages})\n"]
    for row in rows:
        sid, uid, url, t, status = row
        text.append(f"ID:{sid} | User:{uid} | {status} | {t}\n🔗 {url}")
    # inline nav
    kb = types.InlineKeyboardMarkup()
    if page > 1:
        kb.add(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"sub_page:{page-1}"))
    if page < pages:
        kb.add(types.InlineKeyboardButton("➡️ Next", callback_data=f"sub_page:{page+1}"))

    bot.send_message(ADMIN_ID, "\n\n".join(text), reply_markup=kb, disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda q: q.data.startswith("sub_page:"))
def sub_page_cb(q: types.CallbackQuery):
    if not is_admin(q.message.chat.id):
        return bot.answer_callback_query(q.id, "Unauthorized")
    page = int(q.data.split(":")[1])
    # simulate command
    class M: pass
    M = types.Message(
        message_id=q.message.message_id,
        from_user=q.from_user,
        date=q.message.date,
        chat=q.message.chat,
        content_type="text",
        options=None
    )
    M.text = f"/submissions {page}"
    M.json = lambda: {}
    admin_submissions(M)
    bot.answer_callback_query(q.id)

@bot.message_handler(commands=['stats'])
def stats(message: types.Message):
    if not is_admin(message.chat.id):
        return
    tu, ts, tc = get_stats()
    bot.send_message(message.chat.id, f"📈 <b>Stats</b>\n👥 Users: <b>{tu}</b>\n📨 Submissions: <b>{ts}</b>\n💰 Total Coins: <b>{tc}</b>")

def _parse_two_ints(args: list) -> Optional[Tuple[int, int]]:
    if len(args) < 2:
        return None
    try:
        return int(args[0]), int(args[1])
    except:
        return None

@bot.message_handler(commands=['addcoins'])
def addcoins(message: types.Message):
    if not is_admin(message.chat.id): return
    args = message.text.strip().split()[1:]
    parsed = _parse_two_ints(args)
    if not parsed:
        return bot.send_message(message.chat.id, "Usage: /addcoins <user_id> <amount>")
    uid, amt = parsed
    update_coins(uid, amt)
    bot.send_message(message.chat.id, f"✅ Added {amt} coins to {uid}")

@bot.message_handler(commands=['removecoins'])
def removecoins(message: types.Message):
    if not is_admin(message.chat.id): return
    args = message.text.strip().split()[1:]
    parsed = _parse_two_ints(args)
    if not parsed:
        return bot.send_message(message.chat.id, "Usage: /removecoins <user_id> <amount>")
    uid, amt = parsed
    update_coins(uid, -abs(amt))
    bot.send_message(message.chat.id, f"✅ Removed {abs(amt)} coins from {uid}")

@bot.message_handler(commands=['setcoins'])
def setcoins(message: types.Message):
    if not is_admin(message.chat.id): return
    args = message.text.strip().split()[1:]
    if len(args) < 2:
        return bot.send_message(message.chat.id, "Usage: /setcoins <user_id> <value>")
    try:
        uid = int(args[0]); val = int(args[1])
    except:
        return bot.send_message(message.chat.id, "❌ Invalid numbers.")
    set_coins(uid, val)
    bot.send_message(message.chat.id, f"✅ Set coins of {uid} to {val}")

@bot.message_handler(commands=['broadcast'])
def broadcast(message: types.Message):
    if not is_admin(message.chat.id): return
    text = message.text.partition(' ')[2].strip()
    if not text:
        return bot.send_message(message.chat.id, "Usage: /broadcast <message text>")
    # fetch all user ids
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        users = [r[0] for r in c.fetchall()]
    sent, fail = 0, 0
    for uid in users:
        try:
            bot.send_message(uid, f"📢 <b>Broadcast</b>\n\n{text}")
            sent += 1
        except:
            fail += 1
        time.sleep(0.03)  # be gentle
    bot.send_message(message.chat.id, f"✅ Broadcast sent. OK: {sent}, Fail: {fail}")

@bot.message_handler(commands=['export'])
def export_csv(message: types.Message):
    if not is_admin(message.chat.id): return
    fname = f"submissions_{int(time.time())}.csv"
    with db_connect() as conn, open(fname, "w", newline="", encoding="utf-8") as f:
        c = conn.cursor()
        c.execute("SELECT id, user_id, url, time, status FROM submissions ORDER BY id DESC")
        writer = csv.writer(f)
        writer.writerow(["id", "user_id", "url", "time", "status"])
        writer.writerows(c.fetchall())
    with open(fname, "rb") as f:
        bot.send_document(message.chat.id, f, visible_file_name=fname)

# ---------------- FALLBACK ----------------
@bot.message_handler(content_types=['text'])
def fallback(message: types.Message):
    global_rate_limit()
    bot.send_message(
        message.chat.id,
        "मैं आपकी बात समझ नहीं पाया। मेन्यू से चुनें या /help देखें।",
        reply_markup=main_menu()
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    print("🤖 Bot is running...")
    # Long polling; you can switch to webhook for production behind HTTPS
    bot.infinity_polling(timeout=60, long_polling_timeout=60)