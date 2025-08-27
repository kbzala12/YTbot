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

# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    coins INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    daily_points INTEGER DEFAULT 0,
    referred_by INTEGER
)
""")

# Submissions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    url TEXT,
    status TEXT DEFAULT 'pending'
)
""")
conn.commit()

# ---------- HELPERS ----------
def get_user(user_id):
    cursor.execute("SELECT username, coins, referrals, daily_points, referred_by FROM users WHERE id=?", (user_id,))
    return cursor.fetchone()

def add_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def add_coins(user_id, amount):
    cursor.execute("UPDATE users SET coins = coins + ?, daily_points = daily_points + ? WHERE id=?", 
                   (amount, amount, user_id))
    conn.commit()

def add_referral(ref_id, user_id):
    cursor.execute("UPDATE users SET referrals = referrals + 1, coins = coins + ? WHERE id=?", (REFERRAL_POINTS, ref_id))
    cursor.execute("UPDATE users SET referred_by = ? WHERE id=?", (ref_id, user_id))
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
        user = get_user(user_id)
        if ref_id != user_id and user[4] is None:  # referred_by is None
            add_referral(ref_id, user_id)
            bot.send_message(ref_id, f"🎉 आपके referral से नए user ने join किया! आपको {REFERRAL_POINTS} Coins मिले ✅")

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
• हर नए यूज़र पर {REFERRAL_POINTS} पॉइंट्स  

⚠️ *महत्वपूर्ण:*  
बॉट यूज़ करने के लिए पहले ग्रुप जॉइन करना ज़रूरी है।  

Welcome 😊
"""

    # Inline buttons
    inline_kb = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🎬 Open WebApp", url=WEB_URL)
    invite_btn = types.InlineKeyboardButton("👥 Invite Friends", url=f"https://t.me/{BOT_USERNAME}?start={user_id}")
    inline_kb.add(web_btn, invite_btn)

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
    
    username, coins, refs, daily_points, _ = user
    text = message.text

    if text == "🏠 Home":
        bot.send_message(user_id, f"🎬 Open WebApp: {WEB_URL}")
    
    elif text == "🎁 Daily Bonus":
        bonus = min(30, 100 - daily_points)
        if bonus > 0:
            add_coins(user_id, bonus)
            bot.send_message(user_id, f"🎁 आपने {bonus} Coins Daily Bonus में पाए ✅")
        else:
            bot.send_message(user_id, "⚠️ आज की daily limit पूरी हो गई है। कल फिर कोशिश करें!")

    elif text == "🧑‍🤝‍🧑 Invite":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.send_message(user_id, f"🔗 आपका Referral Link:\n{ref_link}\nहर invite पर {REFERRAL_POINTS} Coins!")

    elif text == "👤 Profile":
        text = f"""
👤 *Profile*  

🆔 ID: `{user_id}`  
💳 Balance: *{coins} Coins*  
📅 Daily Points: *{daily_points}*  
👥 Referrals: *{refs}*  
"""
        bot.send_message(user_id, text, parse_mode="Markdown")

    elif text == "💰 Wallet":
        bot.send_message(user_id, f"💳 आपके Wallet में Coins: {coins}")

    elif text == "📤 Submit URL":
        if coins < LINK_SUBMIT_COST:
            bot.send_message(user_id, f"❌ आपके पास {LINK_SUBMIT_COST} Coins नहीं हैं।")
        else:
            msg = bot.send_message(user_id, "📤 अपना लिंक भेजें (https:// से शुरू होना चाहिए):")
            bot.register_next_step_handler(msg, submit_url)
    else:
        bot.send_message(user_id, "❌ Invalid Option! नीचे के buttons इस्तेमाल करें।")

def submit_url(message):
    user_id = message.chat.id
    url = message.text.strip()

    if not url.startswith("https://"):
        bot.send_message(user_id, "❌ केवल valid https URL भेजें।")
        return

    add_coins(user_id, -LINK_SUBMIT_COST)
    cursor.execute("INSERT INTO submissions (user_id, url) VALUES (?, ?)", (user_id, url))
    conn.commit()

    bot.send_message(user_id, f"✅ आपका लिंक भेज दिया गया:\n{url}")
    bot.send_message(ADMIN_ID, f"🔔 नया URL submit: {url}\nUser ID: {user_id}")

# ---------- ADMIN PANEL ----------
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Access Denied.")
    
    cursor.execute("SELECT COUNT(*), SUM(coins) FROM users")
    total_users, total_coins = cursor.fetchone()
    total_users = total_users or 0
    total_coins = total_coins or 0

    cursor.execute("SELECT id, user_id, url, status FROM submissions WHERE status='pending'")
    submissions = cursor.fetchall()

    report = f"""
📊 *Admin Panel*  

👥 Total Users: *{total_users}*  
💰 Total Coins Given: *{total_coins}*  

📝 Pending Submissions: {len(submissions)}
"""
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

    for sub in submissions:
        sub_id, u_id, url, status = sub
        bot.send_message(message.chat.id, f"ID: {sub_id}\nUser ID: {u_id}\nURL: {url}\nStatus: {status}")

# ---------- RUN ----------
print("🤖 Bot is running...")
bot.infinity_polling()