import os
import telebot
from telebot import types
import sqlite3
from config import *

# ---------- BOT INIT ----------
bot = telebot.TeleBot(BOT_TOKEN)

# ---------- KEEP ALIVE ----------
from keep_alive import keep_alive
keep_alive()

# ---------- DB SETUP ----------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    coins INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    last_claim DATE
)
""")

# URLs Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    url TEXT
)
""")
conn.commit()

# ---------- HELPERS ----------
def get_user(user_id):
    cursor.execute("SELECT username, coins, referrals, last_claim FROM users WHERE id=?", (user_id,))
    return cursor.fetchone()

def add_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def add_coins(user_id, amount):
    cursor.execute("UPDATE users SET coins = coins + ? WHERE id=?", (amount, user_id))
    conn.commit()

def add_referral(ref_id):
    cursor.execute("UPDATE users SET referrals = referrals + 1, coins = coins + 100 WHERE id=?", (ref_id,))
    conn.commit()

def add_url(user_id, url):
    cursor.execute("INSERT INTO urls (user_id, url) VALUES (?, ?)", (user_id, url))
    conn.commit()

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.from_user.username or message.from_user.first_name
    add_user(user_id, username)

    # Referral check
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id != user_id:
            add_referral(ref_id)
            bot.send_message(ref_id, f"🎉 आपके referral से नया user जुड़ा! आपको 100 Coins मिले ✅")

    # Welcome text
    welcome_text = f"""
🎬 *Video Coin Earner Bot* 🎬

नमस्ते {message.from_user.first_name}!  

📹 वीडियो देखो, कॉइन कमाओ और  
💰 अपना YouTube चैनल मोनेटाइजेशन करवाओ ✅
"""

    # Inline buttons
    inline_kb = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🎬 Open WebApp", url=WEB_URL)
    invite_btn = types.InlineKeyboardButton("👥 Invite Friends", url=f"https://t.me/{BOT_USERNAME}?start={user_id}")
    group_btn = types.InlineKeyboardButton("📌 Join Group", url=GROUP_URL)
    inline_kb.add(web_btn, invite_btn, group_btn)

    bot.send_message(user_id, welcome_text, parse_mode="Markdown", reply_markup=inline_kb)

    # Reply Keyboard
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("💰 Wallet", "📤 Submit URL")
    menu.row("🎁 Daily Claim", "🧑‍🤝‍🧑 Invite")
    menu.row("👨‍💻 Admin Panel") if user_id == ADMIN_ID else None
    bot.send_message(user_id, "👇 नीचे दिए गए बटन से आगे बढ़ें:", reply_markup=menu)

# ---------- MESSAGE HANDLER ----------
import datetime

@bot.message_handler(func=lambda msg: True)
def handle_buttons(message):
    user_id = message.chat.id
    user = get_user(user_id)
    if not user:
        return bot.send_message(user_id, "❌ पहले /start दबाएँ।")

    username, coins, refs, last_claim = user
    text = message.text

    if text == "💰 Wallet":
        bot.send_message(user_id, f"💳 आपके Wallet में: {coins} Coins")
    
    elif text == "🎁 Daily Claim":
        today = datetime.date.today().isoformat()
        if last_claim == today:
            bot.send_message(user_id, "⚠️ आपने आज का Daily Claim ले लिया है। कल फिर से आएं!")
        else:
            add_coins(user_id, 70)
            cursor.execute("UPDATE users SET last_claim=? WHERE id=?", (today, user_id))
            conn.commit()
            bot.send_message(user_id, "🎁 आपने आज के लिए 70 Coins Claim किए ✅")

    elif text == "🧑‍🤝‍🧑 Invite":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.send_message(user_id, f"🔗 आपका Referral Link:\n{ref_link}\nहर नए user पर 100 Coins!")

    elif text == "📤 Submit URL":
        if coins < 1280:
            bot.send_message(user_id, f"❌ आपके पास 1280 Coins नहीं हैं।")
        else:
            msg = bot.send_message(user_id, "📤 अपना लिंक भेजें (1280 Coins में):")
            bot.register_next_step_handler(msg, submit_url)

    elif text == "👨‍💻 Admin Panel" and user_id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*), SUM(coins) FROM users")
        total_users, total_coins = cursor.fetchone()
        cursor.execute("SELECT url FROM urls")
        urls = cursor.fetchall()
        urls_text = "\n".join([u[0] for u in urls]) if urls else "❌ कोई URL नहीं"
        report = f"""
📊 *Admin Panel*  

👥 Total Users: *{total_users or 0}*  
💰 Total Coins Circulating: *{total_coins or 0}*  

📤 Submitted URLs:  
{urls_text}
"""
        bot.send_message(user_id, report, parse_mode="Markdown")

def submit_url(message):
    user_id = message.chat.id
    url = message.text
    add_coins(user_id, -1280)
    add_url(user_id, url)
    bot.send_message(user_id, f"✅ आपका लिंक submit हुआ: {url}")
    bot.send_message(ADMIN_ID, f"🔔 नया URL:\n{url}\nUser ID: {user_id}")

# ---------- RUN ----------
print("🤖 Bot is running 24/7...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)