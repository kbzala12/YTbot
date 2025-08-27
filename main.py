import telebot
from telebot import types
import sqlite3
from config import *
from keep_alive import keep_alive

# ✅ Bot initialize
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
keep_alive()

# ---------------- User Functions ----------------
def add_user(user_id, ref_id=None):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    # नए user को 50 coin दें
    c.execute("INSERT OR IGNORE INTO users (user_id, coins, referrals) VALUES (?, ?, ?)", (user_id, 50, 0))
    conn.commit()

    # Referral coin
    if ref_id and ref_id != user_id:
        c.execute("UPDATE users SET coins = coins + ?, referrals = referrals + 1 WHERE user_id=?", (REFERRAL_POINTS, ref_id))
        conn.commit()
        bot.send_message(ref_id, f"🎉 आपके referral से नया यूज़र जुड़ा! आपको {REFERRAL_POINTS} पॉइंट्स मिले।")
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

# ---------------- Start Command ----------------
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    user_id = message.chat.id
    add_user(user_id, ref_id)

    # Welcome message
    welcome_text = f"""
🎬 Video Coin Earner Bot में आपका स्वागत है! 🎬

नमस्ते {message.from_user.first_name}!

📹 वीडियो देखो, कॉइन कमाओ और 
💰 अपना YouTube चैनल मोनेटाइजेशन करवाओ ✅

📌 कमाई नियम:
• प्रत्येक वीडियो = 30 पॉइंट्स
• दैनिक लिमिट = 100 पॉइंट्स

👥 रेफरल सिस्टम:
• दोस्तों को इनवाइट करें
• हर नए यूज़र पर {REFERRAL_POINTS} पॉइंट्स

🔗 आपका Referral Link:
https://t.me/{BOT_USERNAME}?start={user_id}

💰 आपका टोटल Coin: {get_coins(user_id)}
"""

    # Keyboard
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🌐 Open WebApp", url=WEB_URL))
    keyboard.add(types.InlineKeyboardButton("📢 Join Group", url="https://t.me/boomupbot10"))
    keyboard.add(types.InlineKeyboardButton("🎁 Invite Friends", url=f"https://t.me/{BOT_USERNAME}?start={user_id}"))

    bot.send_message(user_id, welcome_text, reply_markup=keyboard)

# ---------------- Balance Command ----------------
@bot.message_handler(commands=['balance'])
def balance(message):
    coins = get_coins(message.chat.id)
    bot.send_message(message.chat.id, f"💰 आपके पास {coins} पॉइंट्स हैं।")

# ---------------- Submit URL ----------------
@bot.message_handler(commands=['submit'])
def submit(message):
    user_id = message.chat.id
    coins = get_coins(user_id)
    if coins < LINK_SUBMIT_COST:
        bot.send_message(user_id, f"⚠️ पर्याप्त पॉइंट्स नहीं हैं! आपको {LINK_SUBMIT_COST} पॉइंट्स चाहिए।")
        return
    msg = bot.send_message(user_id, "🔗 अपना YouTube URL भेजें:")
    bot.register_next_step_handler(msg, process_url)

def process_url(message):
    user_id = message.chat.id
    url = message.text
    coins = get_coins(user_id)
    if coins >= LINK_SUBMIT_COST:
        update_coins(user_id, -LINK_SUBMIT_COST)
        conn = sqlite3.connect("bot.db")
        c = conn.cursor()
        c.execute("INSERT INTO submissions (user_id, url) VALUES (?, ?)", (user_id, url))
        conn.commit()
        conn.close()
        bot.send_message(user_id, "✅ आपका URL सबमिट हो गया।")
        bot.send_message(ADMIN_ID, f"📩 New URL Submission:\nUser: {user_id}\nURL: {url}")
    else:
        bot.send_message(user_id, "⚠️ पर्याप्त पॉइंट्स नहीं हैं।")

# ---------------- Admin Panel ----------------
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ सिर्फ़ Admin के लिए।")
        return
    # Admin keyboard
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("💰 Total Coins", "📩 Submissions")
    bot.send_message(message.chat.id, "⚙️ Admin Panel Opened:", reply_markup=keyboard)

# ---------------- Run Bot ----------------
keep_alive()
bot.infinity_polling()