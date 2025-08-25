import telebot
from telebot import types
import sqlite3

# ---------------- CONFIG ----------------
BOT_TOKEN = "PUT-YOUR-TOKEN-HERE"   # 🔑 BotFather से लिया असली Token यहां डालो
ADMIN_ID = 123456789                # अपना Telegram User ID यहां डालो
BOT_USERNAME = "YourBotUsername"    # बिना @ के (जैसे: MyBot123)
WEB_URL = "https://yourwebapp.com"  # अगर WebApp नहीं है तो खाली छोड़ सकते हो

# ---------------- POINT SYSTEM ----------------
DAILY_POINT_LIMIT = 100
VIDEO_POINTS = 30
REFERRAL_POINTS = 100

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0,
        daily_points INTEGER DEFAULT 0,
        ref_id INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

# ---------------- USER CHECK ----------------
def check_user(user_id, ref_id=None):
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cur.fetchone()

    if not user:
        cur.execute("INSERT INTO users (user_id, points, daily_points, ref_id) VALUES (?, ?, ?, ?)",
                    (user_id, 0, 0, ref_id))
        conn.commit()

        # Referrer को points देना
        if ref_id:
            cur.execute("UPDATE users SET points = points + ?, daily_points = daily_points + ? WHERE user_id=?",
                        (REFERRAL_POINTS, REFERRAL_POINTS, ref_id))
            conn.commit()
            try:
                bot.send_message(ref_id, f"🎉 आपके referral से नया user जुड़ा!\nआपको {REFERRAL_POINTS} पॉइंट्स मिले।")
            except:
                pass

    conn.close()

# ---------------- START COMMAND ----------------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    check_user(user_id, ref_id)

    welcome_text = f"""
👋 नमस्ते {message.from_user.first_name}!
🎬 Video Coin Earner Bot में आपका स्वागत है। 

📌 कमाई नियम:
• प्रत्येक वीडियो = {VIDEO_POINTS} पॉइंट्स  
• दैनिक लिमिट = {DAILY_POINT_LIMIT} पॉइंट्स  
• हर रेफरल पर = {REFERRAL_POINTS} पॉइंट्स  

आपका ID: {user_id}
"""

    markup = types.InlineKeyboardMarkup()
    if WEB_URL:
        web_btn = types.InlineKeyboardButton("🚀 Open WebApp", url=WEB_URL)
        markup.add(web_btn)
    invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    invite_btn = types.InlineKeyboardButton("🔗 Invite Friends", url=invite_link)
    markup.add(invite_btn)

    bot.send_message(user_id, welcome_text, reply_markup=markup)

    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 प्रोफाइल", "🎁 पॉइंट्स पाओ")
    menu.row("💰 Wallet")
    bot.send_message(user_id, "👇 नीचे से चुनें:", reply_markup=menu)

# ---------------- MENU HANDLER ----------------
@bot.message_handler(func=lambda msg: True)
def handle_all(message):
    user_id = message.from_user.id
    check_user(user_id)
    text = message.text

    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()

    if text == "📊 प्रोफाइल":
        cur.execute("SELECT points, daily_points FROM users WHERE user_id=?", (user_id,))
        points, dpoints = cur.fetchone()
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.reply_to(message, f"👤 आपके पॉइंट्स: {points}\n📅 आज: {dpoints}/{DAILY_POINT_LIMIT}\n\n🔗 Referral Link:\n{ref_link}")

    elif text == "🎁 पॉइंट्स पाओ":
        cur.execute("SELECT points, daily_points FROM users WHERE user_id=?", (user_id,))
        points, dpoints = cur.fetchone()

        if dpoints + VIDEO_POINTS <= DAILY_POINT_LIMIT:
            new_points = points + VIDEO_POINTS
            new_dpoints = dpoints + VIDEO_POINTS
            cur.execute("UPDATE users SET points=?, daily_points=? WHERE user_id=?", 
                        (new_points, new_dpoints, user_id))
            conn.commit()
            bot.reply_to(message, f"✅ आपको {VIDEO_POINTS} पॉइंट्स मिले! (आज {new_dpoints}/{DAILY_POINT_LIMIT})")
        else:
            bot.reply_to(message, "⚠️ आज की लिमिट पूरी हो चुकी है।")

    elif text == "💰 Wallet":
        cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cur.fetchone()[0]
        bot.reply_to(message, f"💵 Wallet Balance: {points} पॉइंट्स")

    elif text == "👑 Admin":
        if user_id == ADMIN_ID:
            bot.reply_to(message, "✅ आप Admin हैं!")
        else:
            bot.reply_to(message, "⛔ सिर्फ़ Admin के लिए।")

    conn.close()

# ---------------- RUN BOT ----------------
print("🤖 Bot is running...")
bot.infinity_polling()