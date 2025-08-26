import os
import telebot
import sqlite3
from telebot import types
from config import *

# ---------- BOT INIT ----------
bot = telebot.TeleBot(BOT_TOKEN)

# ---------- DB SETUP ----------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    coins INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0
)
""")
conn.commit()

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # अगर user नया है तो DB में डाल दो
    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (id, username, coins, referrals) VALUES (?, ?, ?, ?)", 
                       (user_id, username, 0, 0))
        conn.commit()

    # Referral check
    args = message.text.split()
    if len(args) > 1:
        ref_id = int(args[1])
        if ref_id != user_id:
            cursor.execute("UPDATE users SET referrals = referrals + 1, coins = coins + ? WHERE id=?", 
                           (REFERRAL_POINTS, ref_id))
            conn.commit()

    # Welcome Text
    welcome_text = f"""
🎬 *Video Coin Earner Bot में आपका स्वागत है!* 🎬

नमस्ते {message.from_user.first_name}!  

📹 वीडियो देखो, कॉइन कमाओ और  
💰 अपना YouTube चैनल मोनेटाइजेशन करवाओ ✅  

📌 *कमाई नियम:*  
• प्रत्येक वीडियो = 30 पॉइंट्स  
• दैनिक लिमिट = 100 पॉइंट्स  

👥 *रेफरल सिस्टम:*  
• दोस्तों को इनवाइट करें  
• हर नए यूज़र पर 100 पॉइंट्स  

⚠️ *महत्वपूर्ण:*  
बॉट यूज़ करने के लिए पहले ग्रुप जॉइन करना ज़रूरी है।  

Welcome 😊
"""

    # Buttons
    keyboard = types.InlineKeyboardMarkup()
    open_btn = types.InlineKeyboardButton("🎬 Open WebApp", url=WEB_URL)
    invite_btn = types.InlineKeyboardButton("👥 Invite Friends", 
                                            url=f"https://t.me/{BOT_USERNAME}?start={user_id}")
    keyboard.add(open_btn)
    keyboard.add(invite_btn)

    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- PROFILE ----------
@bot.message_handler(commands=['me'])
def profile(message):
    user_id = message.from_user.id
    cursor.execute("SELECT coins, referrals FROM users WHERE id=?", (user_id,))
    data = cursor.fetchone()
    if data:
        coins, refs = data
        text = f"""
👤 *Profile*  

🆔 ID: `{user_id}`  
💳 Balance: *{coins} Coins*  
👥 Referrals: *{refs}*  
"""
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ आप अभी तक register नहीं हुए। /start दबाएँ।")

# ---------- ADMIN PANEL ----------
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Access Denied.")

    cursor.execute("SELECT COUNT(*), SUM(coins) FROM users")
    total_users, total_coins = cursor.fetchone()
    total_users = total_users or 0
    total_coins = total_coins or 0

    report = f"""
📊 *Admin Panel*  

👥 Total Users: *{total_users}*  
💰 Total Coins Given: *{total_coins}*  
"""
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

# ---------- RUN ----------
print("🤖 Bot is running...")
bot.infinity_polling()