import telebot
from telebot import types
import sqlite3
from config import *

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- Database Setup ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        points INTEGER DEFAULT 0
    )''')
    conn.commit()
    return conn, cur

conn, cur = init_db()

# ---------------- /start Command ----------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    cur.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

    markup = types.InlineKeyboardMarkup()
    # WebApp Button
    markup.add(types.InlineKeyboardButton("🌐 Open WebApp", url=WEB_URL))
    # Invite Button
    markup.add(types.InlineKeyboardButton("👥 Invite & Earn 100 Coins", switch_inline_query=""))

    bot.send_message(message.chat.id,
                     f"नमस्ते @{username}! 🎬\n\nWebApp खोलने के लिए नीचे क्लिक करें और वीडियो देखें।",
                     reply_markup=markup)

# ---------------- Video Watch Simulation ----------------
@bot.message_handler(commands=['watch'])
def watch_video(message):
    user_id = message.from_user.id
    cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if row:
        points = row[0] + VIDEO_POINTS
        cur.execute("UPDATE users SET points=? WHERE user_id=?", (points, user_id))
        conn.commit()
        bot.reply_to(message, f"🎉 आपने {VIDEO_POINTS} पॉइंट्स कमाए! कुल पॉइंट्स: {points}")
    else:
        bot.reply_to(message, "कृपया /start करें पहले।")

bot.infinity_polling()