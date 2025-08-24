import telebot
from telebot import types
import sqlite3
import datetime
from config import *
from keep_alive import keep_alive

bot = telebot.TeleBot(BOT_TOKEN)
keep_alive()  # Optional for 24/7

# Database Init
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0,
        daily_points INTEGER DEFAULT 0,
        last_active TEXT,
        ref_id INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

# User check & referral
def check_user(user_id, ref_id=None):
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    today = datetime.date.today().isoformat()

    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cur.fetchone()

    if not user:
        cur.execute("INSERT INTO users (user_id, points, daily_points, last_active, ref_id) VALUES (?, ?, ?, ?, ?)",
                    (user_id, 0, 0, today, ref_id))
        conn.commit()
        if ref_id and ref_id != user_id:
            cur.execute("UPDATE users SET points = points + ?, daily_points = daily_points + ? WHERE user_id=?",
                        (REFERRAL_POINTS, REFERRAL_POINTS, ref_id))
            conn.commit()
            bot.send_message(ref_id, f"🎉 आपके referral से नया यूज़र जुड़ा! आपको {REFERRAL_POINTS} कॉइन मिले।")
    else:
        last_active = user[3]
        if last_active != today:
            cur.execute("UPDATE users SET daily_points=?, last_active=? WHERE user_id=?", (0, today, user_id))
            conn.commit()
    conn.close()

# /start Command
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    check_user(user_id, ref_id)

    welcome_text = f"""
🎉 नमस्ते {message.from_user.first_name}!
🚀 WebApp खोलें, ग्रुप जॉइन करें, और दोस्तों को इनवाइट करें।
"""
    markup = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🚀 Open WebApp", url=WEB_URL)
    group_btn = types.InlineKeyboardButton("📌 Join Group", url="https://t.me/boomupbot10")
    invite_btn = types.InlineKeyboardButton("🔗 Invite Friends", url=f"https://t.me/{BOT_USERNAME}?start={user_id}")
    markup.add(web_btn, group_btn, invite_btn)
    bot.send_message(user_id, welcome_text, reply_markup=markup)

    # Menu
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 Profile", "💰 Wallet")
    menu.row("🔗 Invite Friends", "📤 URL Submit")
    bot.send_message(user_id, "👇 नीचे बटन से आगे बढ़ें:", reply_markup=menu)

# Menu handler
@bot.message_handler(func=lambda msg: True)
def handle_menu(message):
    user_id = message.from_user.id
    text = message.text
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()

    if text == "📊 Profile":
        cur.execute("SELECT points, daily_points FROM users WHERE user_id=?", (user_id,))
        points, dpoints = cur.fetchone()
        bot.send_message(user_id, f"👤 Points: {points}\n📅 Daily Earned: {dpoints}")

    elif text == "💰 Wallet":
        cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cur.fetchone()[0]
        bot.send_message(user_id, f"💵 Wallet Balance: {points} कॉइन")

    elif text == "🔗 Invite Friends":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.send_message(user_id, f"👥 अपने दोस्तों को इनवाइट करें!\nReferral Link:\n{ref_link}\n100 कॉइन मिलेंगे ✅")

    elif text == "📤 URL Submit":
        cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cur.fetchone()[0]
        if points >= LINK_SUBMIT_COST:
            bot.send_message(user_id, "📌 YouTube URL भेजें:")
            bot.register_next_step_handler(message, process_url)
        else:
            bot.send_message(user_id, f"⚠️ {LINK_SUBMIT_COST} कॉइन चाहिए। आपके पास: {points}")

    conn.close()

# URL submit
def process_url(message):
    user_id = message.from_user.id
    url = message.text
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    points = cur.fetchone()[0]

    if points >= LINK_SUBMIT_COST:
        new_points = points - LINK_SUBMIT_COST
        cur.execute("UPDATE users SET points=? WHERE user_id=?", (new_points, user_id))
        conn.commit()
        bot.send_message(user_id, f"✅ आपका URL submit हो गया, {LINK_SUBMIT_COST} कॉइन कटे।")
        bot.send_message(ADMIN_ID, f"📩 New URL Submission\nUser ID: {user_id}\nURL: {url}\nCost: {LINK_SUBMIT_COST} कॉइन")
    else:
        bot.send_message(user_id, "⚠️ पर्याप्त कॉइन नहीं।")
    conn.close()

# Run Bot
bot.infinity_polling()