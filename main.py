import telebot
from telebot import types
import sqlite3
from config import *
from keep_alive import keep_alive

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- Database ----------------
def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 0,
                referrals INTEGER DEFAULT 0
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT,
                status TEXT DEFAULT 'pending'
                )""")
    conn.commit()
    conn.close()

init_db()

# ---------------- User Functions ----------------
def add_user(user_id, ref_id=None):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, coins, referrals) VALUES (?, ?, ?)", (user_id, 50, 0))
    conn.commit()
    if ref_id and ref_id != user_id:
        c.execute("UPDATE users SET coins = coins + 100, referrals = referrals + 1 WHERE user_id=?", (ref_id,))
        conn.commit()
        bot.send_message(ref_id, f"🎉 आपके referral से नया यूज़र जुड़ा! आपको 100 कॉइन मिले।")
    conn.close()

def get_coins(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
    coins = c.fetchone()
    conn.close()
    return coins[0] if coins else 0

def update_coins(user_id, amount):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def get_total_users():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT user_id, coins, referrals FROM users")
    users = c.fetchall()
    conn.close()
    return users

# ---------------- Start Command ----------------
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    user_id = message.chat.id
    add_user(user_id, ref_id)

    # Inline buttons
    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(types.InlineKeyboardButton("🌐 Open WebApp", url=WEB_URL))
    inline_kb.add(types.InlineKeyboardButton("📢 Join Group", url="https://t.me/boomupbot10"))
    inline_kb.add(types.InlineKeyboardButton("🎁 Invite Friends", url=f"https://t.me/{bot.get_me().username}?start={user_id}"))

    bot.send_message(user_id,
        "😊 Welcome!\n\n"
        "🎬 Video Dekho 🔥 Coin Kamvo\n"
        "💰 Apna YouTube Channel Monetization Karvao ✅\n\n"
        f"💰 आपका बैलेंस: {get_coins(user_id)} कॉइन\n\n"
        "👇 नीचे बटन से WebApp खोलें और ग्रुप जॉइन करें:\n\n"
        f"🔗 आपका Referral Link:\nhttps://t.me/{bot.get_me().username}?start={user_id}",
        reply_markup=inline_kb
    )

    # User Keyboard
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 Profile", "💰 Wallet")
    menu.row("📤 Submit URL", "📢 Subscribe")
    if user_id == ADMIN_ID:
        menu.row("📊 Total Users", "⚙️ Admin Panel")
    bot.send_message(user_id, "👇 नीचे दिए गए बटन से आगे बढ़ें:", reply_markup=menu)

# ---------------- Profile ----------------
@bot.message_handler(func=lambda m: m.text == "📊 Profile")
def profile(message):
    coins = get_coins(message.chat.id)
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT referrals FROM users WHERE user_id=?", (message.chat.id,))
    ref = c.fetchone()[0]
    conn.close()
    bot.send_message(message.chat.id, f"👤 Coins: {coins}\n👥 Referrals: {ref}")

# ---------------- Wallet ----------------
@bot.message_handler(func=lambda m: m.text == "💰 Wallet")
def wallet(message):
    coins = get_coins(message.chat.id)
    bot.send_message(message.chat.id, f"💵 आपके Wallet में {coins} कॉइन हैं।")

# ---------------- Subscribe ----------------
@bot.message_handler(func=lambda m: m.text == "📢 Subscribe")
def subscribe(message):
    bot.send_message(message.chat.id, "📺 हमारे VIP YouTube चैनल को Subscribe करें:\n👉 https://youtube.com/@kishorsinhzala.?si=7Hmmk0GlISdW9VsF")

# ---------------- URL Submit ----------------
@bot.message_handler(func=lambda m: m.text == "📤 Submit URL")
def submit(message):
    coins = get_coins(message.chat.id)
    if coins < 1280:
        bot.send_message(message.chat.id, "⚠️ पर्याप्त कॉइन नहीं हैं (1280 चाहिए)।")
        return
    msg = bot.send_message(message.chat.id, "🔗 अपना YouTube URL भेजें:")
    bot.register_next_step_handler(msg, process_url)

def process_url(message):
    user_id = message.chat.id
    url = message.text
    coins = get_coins(user_id)
    if coins >= 1280:
        update_coins(user_id, -1280)
        conn = sqlite3.connect("bot.db")
        c = conn.cursor()
        c.execute("INSERT INTO submissions (user_id, url) VALUES (?, ?)", (user_id, url))
        conn.commit()
        conn.close()
        bot.send_message(user_id, "✅ आपका URL सबमिट हो गया।")
        bot.send_message(ADMIN_ID, f"📩 New URL Submission:\nUser: {user_id}\nURL: {url}")
    else:
        bot.send_message(user_id, "⚠️ पर्याप्त कॉइन नहीं हैं।")

# ---------------- Admin Commands ----------------
@bot.message_handler(func=lambda m: m.text == "📊 Total Users" and m.chat.id == ADMIN_ID)
def total_users(message):
    users = get_total_users()
    text = f"📊 Total Users: {len(users)}\n\n"
    for u in users:
        text += f"User: {u[0]} | Coins: {u[1]} | Referrals: {u[2]}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel" and m.chat.id == ADMIN_ID)
def admin_panel(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("✅ Approve", "❌ Reject")
    keyboard.row("📊 Total Users")
    bot.send_message(message.chat.id, "⚙️ Admin Panel Ready", reply_markup=keyboard)

# ---------------- Run Bot ----------------
keep_alive()
bot.infinity_polling()