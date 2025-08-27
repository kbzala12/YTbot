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
    if ref_id:
        c.execute("UPDATE users SET coins = coins + 100, referrals = referrals + 1 WHERE user_id=?", (ref_id,))
        conn.commit()
        bot.send_message(ref_id, f"🎉 आपको रेफ़रल से 100 कॉइन मिले! नया यूज़र जुड़ा।")
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

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🌐 Open WebApp", url=WEB_URL))
    keyboard.add(types.InlineKeyboardButton("📢 Join Group", url="https://t.me/boomupbot10"))
    keyboard.add(types.InlineKeyboardButton("🎁 Invite Friends", url=f"https://t.me/{bot.get_me().username}?start={user_id}"))

    bot.send_message(user_id,
        f"👋 स्वागत है {message.from_user.first_name}!\n"
        f"💰 आपका बैलेंस: {get_coins(user_id)} कॉइन\n\n"
        "नीचे बटन से WebApp खोलें और ग्रुप जॉइन करें:",
        reply_markup=keyboard
    )

# ---------------- Check Balance ----------------
@bot.message_handler(commands=['balance'])
def balance(message):
    coins = get_coins(message.chat.id)
    bot.send_message(message.chat.id, f"💰 आपके पास {coins} कॉइन हैं।")

# ---------------- Submit URL ----------------
@bot.message_handler(commands=['submit'])
def submit(message):
    user_id = message.chat.id
    coins = get_coins(user_id)
    if coins < 1280:
        bot.send_message(user_id, "⚠️ पर्याप्त कॉइन नहीं हैं (1280 चाहिए)।")
        return
    msg = bot.send_message(user_id, "🔗 अपना YouTube URL भेजें:")
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

# ---------------- Admin Panel ----------------
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ सिर्फ़ Admin के लिए।")
        return
    bot.send_message(message.chat.id, "⚙️ Admin Panel:\n/approve <id>\n/reject <id>")

@bot.message_handler(commands=['approve'])
def approve(message):
    if message.chat.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "ID दे।")
        return
    sub_id = int(args[1])
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE submissions SET status='approved' WHERE id=?", (sub_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Submission {sub_id} approved.")

@bot.message_handler(commands=['reject'])
def reject(message):
    if message.chat.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "ID दे।")
        return
    sub_id = int(args[1])
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE submissions SET status='rejected' WHERE id=?", (sub_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"❌ Submission {sub_id} rejected.")

# ---------------- Run Bot ----------------
keep_alive()
bot.infinity_polling()