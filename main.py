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
    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 50,
                referrals INTEGER DEFAULT 0
                )""")
    # Submissions table
    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT,
                status TEXT DEFAULT 'pending'
                )""")
    conn.commit()
    conn.close()

init_db()
keep_alive()  # Flask server

# ---------------- User Functions ----------------
def add_user(user_id, ref_id=None):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    
    # Add new user
    c.execute("INSERT OR IGNORE INTO users (user_id, coins, referrals) VALUES (?, ?, ?)", (user_id, 50, 0))
    conn.commit()

    # Add referral coins
    if ref_id and ref_id != user_id:
        c.execute("SELECT user_id FROM users WHERE user_id=?", (ref_id,))
        if c.fetchone():
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

# ---------------- Start Command ----------------
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    user_id = message.chat.id
    add_user(user_id, ref_id)

    # Inline keyboard
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🌐 Open WebApp", url=WEB_URL))
    keyboard.add(types.InlineKeyboardButton("📢 Join Group", url="https://t.me/boomupbot10"))
    keyboard.add(types.InlineKeyboardButton("🎁 Invite Friends", url=f"https://t.me/{bot.get_me().username}?start={user_id}"))

    bot.send_message(user_id,
        f"👋 स्वागत है {message.from_user.first_name}!\n"
        f"💰 आपका बैलेंस: {get_coins(user_id)} कॉइन\n\n"
        "👇 नीचे बटन से WebApp खोलें और Group Join करें।",
        reply_markup=keyboard
    )

    # Main menu keyboard
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 Profile", "💰 Wallet")
    menu.row("📤 Submit URL", "📢 Subscribe")
    if user_id == ADMIN_ID:
        menu.row("👑 Admin Panel")
    bot.send_message(user_id, "👇 बटन से आगे बढ़ें:", reply_markup=menu)

# ---------------- Check Balance ----------------
@bot.message_handler(func=lambda m: m.text == "📊 Profile")
def profile(message):
    coins = get_coins(message.chat.id)
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT referrals FROM users WHERE user_id=?", (message.chat.id,))
    ref_count = c.fetchone()[0]
    conn.close()
    bot.send_message(message.chat.id, f"👤 Coins: {coins}\n👥 Referrals: {ref_count}")

@bot.message_handler(func=lambda m: m.text == "💰 Wallet")
def wallet(message):
    coins = get_coins(message.chat.id)
    bot.send_message(message.chat.id, f"💵 आपके Wallet में {coins} कॉइन हैं।")

# ---------------- Submit URL ----------------
@bot.message_handler(func=lambda m: m.text == "📤 Submit URL")
def submit(message):
    user_id = message.chat.id
    coins = get_coins(user_id)
    if coins < LINK_SUBMIT_COST:
        bot.send_message(user_id, f"⚠️ पर्याप्त कॉइन नहीं! {LINK_SUBMIT_COST} चाहिए।")
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
        bot.send_message(user_id, f"✅ URL submit हो गया! {LINK_SUBMIT_COST} कॉइन कटे।")
        bot.send_message(ADMIN_ID, f"📩 New URL Submission\nUser: {user_id}\nURL: {url}")
    else:
        bot.send_message(user_id, "⚠️ पर्याप्त कॉइन नहीं हैं।")

# ---------------- Subscribe ----------------
@bot.message_handler(func=lambda m: m.text == "📢 Subscribe")
def subscribe(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📺 Subscribe VIP Channel", url=VIP_YT_CHANNEL))
    markup.add(types.InlineKeyboardButton("✅ Subscribed", callback_data="sub_done"))
    bot.send_message(message.chat.id, f"🎉 Subscribe करके {SUBSCRIBE_POINTS} कॉइन पाएं:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "sub_done")
def sub_done(call):
    user_id = call.from_user.id
    update_coins(user_id, SUBSCRIBE_POINTS)
    bot.answer_callback_query(call.id, f"✅ {SUBSCRIBE_POINTS} कॉइन जुड़े!")

# ---------------- Admin Panel ----------------
@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel" and m.chat.id == ADMIN_ID)
def admin_panel(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📊 Total Users", "📋 Submissions")
    bot.send_message(message.chat.id, "⚙️ Admin Panel:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "📊 Total Users" and m.chat.id == ADMIN_ID)
def total_users(message):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT user_id, coins, referrals FROM users")
    users = c.fetchall()
    conn.close()
    text = f"📊 Total Users: {len(users)}\n\n"
    for u in users:
        text += f"User: {u[0]} | Coins: {u[1]} | Referrals: {u[2]}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📋 Submissions" and m.chat.id == ADMIN_ID)
def admin_submissions(message):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT id, user_id, url, status FROM submissions")
    subs = c.fetchall()
    conn.close()
    text = "📋 Submissions:\n"
    for s in subs:
        text += f"ID: {s[0]} | User: {s[1]} | URL: {s[2]} | Status: {s[3]}\n"
    bot.send_message(message.chat.id, text)

# ---------------- Run Bot ----------------
keep_alive()
bot.infinity_polling()