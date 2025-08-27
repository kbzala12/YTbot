import telebot
from telebot import types
import sqlite3
from config import *
from keep_alive import keep_alive

# ✅ Bot initialize
bot = telebot.TeleBot(BOT_TOKEN)

# ✅ Database setup
def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 0,
                referrals INTEGER DEFAULT 0
                )""")
    conn.commit()
    conn.close()

init_db()

# ✅ Add user if not exists
def add_user(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, coins, referrals) VALUES (?, ?, ?)", (user_id, 0, 0))
    conn.commit()
    conn.close()

# ✅ Get coins
def get_coins(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# ✅ Update coins
def update_coins(user_id, coins):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET coins=? WHERE user_id=?", (coins, user_id))
    conn.commit()
    conn.close()

# ✅ Start Command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    add_user(user_id)

    keyboard = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🌐 Open WebApp", url=WEB_URL)
    join_btn = types.InlineKeyboardButton("📢 Join Group", url="https://t.me/boomupbot10")
    keyboard.add(web_btn)
    keyboard.add(join_btn)

    bot.send_message(
        user_id,
        f"👋 स्वागत है {message.from_user.first_name}!\n\n"
        f"👉 आपका बैलेंस: {get_coins(user_id)} कॉइन\n\n"
        "👇 नीचे दिए गए बटन से WebApp खोलें और Group Join करें।",
        reply_markup=keyboard
    )

# ✅ Check Balance
@bot.message_handler(commands=['balance'])
def balance(message):
    coins = get_coins(message.chat.id)
    bot.send_message(message.chat.id, f"💰 आपके पास {coins} कॉइन हैं।")

# ✅ Admin Command
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if str(message.chat.id) == str(ADMIN_ID):
        bot.send_message(message.chat.id, "⚙️ Admin Panel Ready!")
    else:
        bot.send_message(message.chat.id, "❌ यह कमांड सिर्फ Admin के लिए है।")

# ✅ Run bot
keep_alive()
bot.polling(non_stop=True)