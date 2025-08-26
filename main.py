# main.py
import os
import telebot
from telebot import types
import sqlite3
from config import *

# ---------- BOT INIT ----------
bot = telebot.TeleBot(BOT_TOKEN)

# ---------- KEEP ALIVE ----------
from keep_alive import keep_alive
keep_alive()

# ---------- DB SETUP ----------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    coins INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    daily_points INTEGER DEFAULT 0
)
""")
conn.commit()

# ---------- HELPERS ----------
def get_user(user_id):
    cursor.execute("SELECT username, coins, referrals, daily_points FROM users WHERE id=?", (user_id,))
    return cursor.fetchone()

def add_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def add_coins(user_id, amount):
    cursor.execute("UPDATE users SET coins = coins + ?, daily_points = daily_points + ? WHERE id=?", 
                   (amount, amount, user_id))
    conn.commit()

def add_referral(ref_id):
    cursor.execute("UPDATE users SET referrals = referrals + 1, coins = coins + 100 WHERE id=?", (ref_id,))
    conn.commit()

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.from_user.username or message.from_user.first_name
    add_user(user_id, username)

    # Referral check
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id != user_id:
            add_referral(ref_id)
            bot.send_message(ref_id, f"🎉 आपके referral से नए user ने join किया! आपको 100 Coins मिले ✅")

    # Welcome Text
    welcome_text = f"""
🎬 *Video Coin Earner Bot में आपका स्वागत है!* 🎬

नमस्ते {message.from_user.first_name}!  

📹 वीडियो देखो, कॉइन कमाओ और  
💰 अपना YouTube चैनल मोनेटाइजेशन करवाओ ✅  

⚠️ *महत्वपूर्ण:*  
बॉट यूज़ करने के लिए पहले ग्रुप जॉइन करना ज़रूरी है।  
"""

    # Inline buttons
    inline_kb = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🎬 Open WebApp", url=WEB_URL)
    group_btn = types.InlineKeyboardButton("👥 Join Group", url=GROUP_URL)
    inline_kb.add(web_btn, group_btn)

    bot.send_message(user_id, welcome_text, parse_mode="Markdown", reply_markup=inline_kb)

    # Reply Keyboard
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("🏠 Home", "🎁 Daily Bonus")
    menu.row("🧑‍🤝‍🧑 Invite", "👤 Profile")
    menu.row("💰 Wallet", "📤 Submit URL")
    bot.send_message(user_id, "👇 नीचे दिए गए बटन से आगे बढ़ें:", reply_markup=menu)

# ---------- MESSAGE HANDLER ----------
@bot.message_handler(func=lambda msg: True)
def handle_buttons(message):
    user_id = message.chat.id
    user = get_user(user_id)
    if not user:
        return bot.send_message(user_id, "❌ पहले /start दबाएँ।")
    
    text = message.text
    if text == "🏠 Home":
        bot.send_message(user_id, f"🎬 Open WebApp: {WEB_URL}")
    elif text == "🎁 Daily Bonus":
        username, coins, refs, daily_points = user
        if daily_points + 30 <= 100:
            add_coins(user_id, 30)
            bot.send_message(user_id, "🎁 आपने 30 Coins Daily Bonus में पाए ✅")
        else:
            bot.send_message(user_id, "⚠️ आज की daily limit पूरी हो गई है। कल फिर कोशिश करें!")
    elif text == "🧑‍🤝‍🧑 Invite":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.send_message(user_id, f"🔗 आपका Referral Link:\n{ref_link}\nहर नए user पर 100 Coins!")
    elif text == "👤 Profile":
        username, coins, refs, daily_points = user
        text = f"""
👤 *Profile*  

🆔 ID: `{user_id}`  
💳 Balance: *{coins} Coins*  
📅 Daily Points: *{daily_points}*  
👥 Referrals: *{refs}*  
"""
        bot.send_message(user_id, text, parse_mode="Markdown")
    elif text == "💰 Wallet":
        username, coins, refs, daily_points = user
        bot.send_message(user_id, f"💳 आपके Wallet में Coins: {coins}")
    elif text == "📤 Submit URL":
        username, coins, refs, daily_points = user
        if coins < 1280:
            bot.send_message(user_id, f"❌ आपके पास 1280 Coins नहीं हैं।")
        else:
            msg = bot.send_message(user_id, "📤 अपना लिंक भेजें (1280 Coins में):")
            bot.register_next_step_handler(msg, submit_url)
    else:
        bot.send_message(user_id, "❌ Invalid Option! नीचे के buttons इस्तेमाल करें।")

def submit_url(message):
    user_id = message.chat.id
    url = message.text
    add_coins(user_id, -1280)  # Deduct 1280 coins
    bot.send_message(user_id, f"✅ आपका लिंक भेज दिया गया:\n{url}")
    bot.send_message(ADMIN_ID, f"🔔 नया URL submit: {url}\nUser ID: {user_id}\nUsername: {message.from_user.username}")

# ---------- ADMIN PANEL ----------
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
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
print("🤖 Bot setup complete. Polling is disabled to prevent running, DB remains active.")
# bot.infinity_polling()  # Commented to prevent running automatically