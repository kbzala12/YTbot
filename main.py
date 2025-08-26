import os
import sqlite3
import telebot
from telebot import types
from datetime import datetime

# ---------------- Bot Credentials ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7978191312:AAFFaOkxBSI9YoN4uR3I5FtZbfQNojT8F4U")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7459795138))
BOT_USERNAME = os.environ.get("BOT_USERNAME", "Bingyt_bot")

# ---------------- Config ----------------
LINK_SUBMIT_COST = 1280
REFERRAL_POINTS = 100
DAILY_BONUS = 10

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- Database ----------------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    name TEXT,
    username TEXT,
    coins INTEGER DEFAULT 0,
    invites INTEGER DEFAULT 0,
    last_bonus TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS urls(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    url TEXT,
    status TEXT DEFAULT 'pending'
)""")
conn.commit()

# ---------------- Helper ----------------
def user_exists(user_id):
    cur.execute("SELECT id FROM users WHERE id=?", (user_id,))
    return cur.fetchone()

def create_user(user):
    if not user_exists(user.id):
        cur.execute("INSERT INTO users (id,name,username,coins,invites) VALUES (?,?,?,?,?)",
                    (user.id, user.first_name, user.username, 0, 0))
        conn.commit()

def get_coins(user_id):
    cur.execute("SELECT coins FROM users WHERE id=?", (user_id,))
    data = cur.fetchone()
    return data[0] if data else 0

def add_coins(user_id, amount):
    cur.execute("UPDATE users SET coins=coins+? WHERE id=?", (amount, user_id))
    conn.commit()

# ---------------- Start ----------------
@bot.message_handler(commands=['start'])
def start(message):
    create_user(message.from_user)
    text = """🎬 *Video Coin Earner Bot में आपका स्वागत है!* 🎬

नमस्ते *{name}* 👋

📹 वीडियो देखो, कॉइन कमाओ और  
💰 अपना YouTube चैनल मोनेटाइजेशन करवाओ ✅  

📌 *कमाई नियम:*
• प्रत्येक वीडियो = 30 पॉइंट्स  
• दैनिक लिमिट = 100 पॉइंट्स  

👥 *रेफरल सिस्टम:*  
• दोस्तों को इनवाइट करें  
• हर नए यूज़र पर 100 पॉइंट्स  

⚠️ महत्वपूर्ण: बॉट यूज़ करने के लिए पहले ग्रुप जॉइन करना ज़रूरी है।
""".format(name=message.from_user.first_name)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🏦 Wallet", "🔗 Submit URL")
    markup.add("🎁 Daily Bonus", "👥 Invite Friends")

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

# ---------------- Wallet ----------------
@bot.message_handler(func=lambda m: m.text == "🏦 Wallet")
def wallet(message):
    cur.execute("SELECT coins,invites FROM users WHERE id=?", (message.from_user.id,))
    data = cur.fetchone()
    coins, invites = data
    text = f"""👤 *Profile Info*

🆔 ID: `{message.from_user.id}`
📛 Name: {message.from_user.first_name}
💰 Coins: {coins}
👥 Invites: {invites}
"""
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ---------------- Daily Bonus ----------------
@bot.message_handler(func=lambda m: m.text == "🎁 Daily Bonus")
def daily_bonus(message):
    user_id = message.from_user.id
    cur.execute("SELECT last_bonus FROM users WHERE id=?", (user_id,))
    last = cur.fetchone()[0]
    today = datetime.now().strftime("%Y-%m-%d")

    if last == today:
        bot.send_message(message.chat.id, "⚠️ आपने आज का बोनस पहले ही ले लिया है।")
    else:
        add_coins(user_id, DAILY_BONUS)
        cur.execute("UPDATE users SET last_bonus=? WHERE id=?", (today, user_id))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ आपको {DAILY_BONUS} कॉइन का दैनिक बोनस मिला!")

# ---------------- Invite Friends ----------------
@bot.message_handler(func=lambda m: m.text == "👥 Invite Friends")
def invite(message):
    bot.send_message(message.chat.id,
                     f"🔗 अपना रेफरल लिंक:\nhttps://t.me/{BOT_USERNAME}?start={message.from_user.id}")

# ---------------- Handle Referral ----------------
@bot.message_handler(commands=['start'], regexp="start ")
def referral(message):
    ref_id = int(message.text.split()[1])
    if ref_id != message.from_user.id and user_exists(ref_id):
        create_user(message.from_user)
        add_coins(ref_id, REFERRAL_POINTS)
        cur.execute("UPDATE users SET invites=invites+1 WHERE id=?", (ref_id,))
        conn.commit()
        bot.send_message(ref_id, f"🎉 नया यूज़र जुड़ा! आपको {REFERRAL_POINTS} कॉइन मिले ✅")

# ---------------- Submit URL ----------------
@bot.message_handler(func=lambda m: m.text == "🔗 Submit URL")
def submit_url(message):
    coins = get_coins(message.from_user.id)
    if coins < LINK_SUBMIT_COST:
        bot.send_message(message.chat.id, f"⚠️ आपको लिंक सबमिट करने के लिए {LINK_SUBMIT_COST} कॉइन चाहिए।")
    else:
        msg = bot.send_message(message.chat.id, "📩 कृपया अपना YouTube लिंक भेजें:")
        bot.register_next_step_handler(msg, save_url)

def save_url(message):
    url = message.text
    user_id = message.from_user.id
    cur.execute("INSERT INTO urls (user_id,url) VALUES (?,?)", (user_id, url))
    cur.execute("UPDATE users SET coins=coins-? WHERE id=?", (LINK_SUBMIT_COST, user_id))
    conn.commit()
    bot.send_message(message.chat.id, "✅ आपका लिंक एडमिन को भेज दिया गया।")
    bot.send_message(ADMIN_ID, f"📥 नया URL सबमिशन:\n\n{url}\n\n👤 User: {message.from_user.first_name} ({user_id})")

# ---------------- Admin Panel ----------------
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ आप एडमिन नहीं हैं।")

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT SUM(coins) FROM users")
    total_coins = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM urls WHERE status='pending'")
    pending = cur.fetchone()[0]

    text = f"""📊 *Admin Panel*

👥 Total Users: {total_users}
💰 Total Coins: {total_coins}
📩 Pending URLs: {pending}
"""

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✅ Approve URL", "❌ Reject URL")
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)


print("🤖 Bot is running...")
bot.infinity_polling()