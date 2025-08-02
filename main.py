import telebot
import sqlite3
import os
from flask import Flask, request
from threading import Thread

# ========== CONFIG ==========
BOT_TOKEN = "8192810260:AAFfhjDfNywZIzkrlVmtAuKFL5_E-ZnsOmU"
ADMIN_ID = 7459795138
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ========== DATABASE ==========
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            points INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ========== TELEGRAM HANDLERS ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id

    # Referral system
    if len(message.text.split()) > 1:
        ref_id = int(message.text.split()[1])
        if ref_id != user_id:
            add_points(ref_id, 50)
            bot.send_message(ref_id, f"🎉 आपने एक नया रेफ़रल प्राप्त किया! +50 पॉइंट्स")

    add_user(user_id)
    bot.send_message(user_id, "🙏 स्वागत है! आपने बॉट शुरू किया है।\nहर वीडियो देखने पर 10 पॉइंट्स मिलेंगे।")

# ========== DATABASE FUNCTIONS ==========
def add_user(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def add_points(user_id, points):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

# ========== FLASK WEBHOOK ==========
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def home():
    return "Bot is running!", 200

# ========== THREAD TO RUN BOT LOCALLY TOO (SAFETY) ==========
def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)