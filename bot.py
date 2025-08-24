# bot.py
import telebot
from telebot import types
import sqlite3
from config import BOT_TOKEN, ADMIN_ID, WEB_URL
from keep_alive import keep_alive

# ===== Bot Config =====
DAILY_POINT_LIMIT = 100
VIDEO_POINTS = 30
REFERRAL_POINTS = 100
BOT_USERNAME = "Bingyt_bot"

bot = telebot.TeleBot(BOT_TOKEN)

# ===== Database Setup =====
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    video_count INTEGER DEFAULT 0,
    daily_points INTEGER DEFAULT 0,
    ref_id INTEGER,
    url_submitted INTEGER DEFAULT 0
)''')
conn.commit()

# ===== Keep Bot Alive =====
keep_alive()

# ===== User Check / Create =====
def check_user(user_id, ref_id=None):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cur.fetchone()
    if not user:
        initial_points = REFERRAL_POINTS if ref_id else 0
        cur.execute("INSERT INTO users (user_id, points, video_count, daily_points, ref_id) VALUES (?, ?, ?, ?, ?)",
                    (user_id, initial_points, 0, initial_points, ref_id))
        conn.commit()
        if ref_id:
            cur.execute("UPDATE users SET points = points + ?, daily_points = daily_points + ? WHERE user_id=?",
                        (REFERRAL_POINTS, REFERRAL_POINTS, ref_id))
            conn.commit()
            bot.send_message(ref_id, f"🎉 आपके referral से नए user ने join किया! आपको {REFERRAL_POINTS} पॉइंट्स मिले।")

# ===== /start Command =====
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    check_user(user_id, ref_id)

    welcome_text = f"""
🎬 Video Coin Earner Bot में आपका स्वागत है! 🎬

नमस्ते {message.from_user.first_name}!

📹 वीडियो देखो, कॉइन कमाओ और  
💰 अपना YouTube चैनल मोनेटाइजेशन करवाओ ✅  

📌 कमाई नियम:
• प्रत्येक वीडियो = {VIDEO_POINTS} पॉइंट्स  
• दैनिक लिमिट = {DAILY_POINT_LIMIT} पॉइंट्स  

👥 रेफरल सिस्टम:  
• दोस्तों को इनवाइट करें  
• हर नए यूज़र पर {REFERRAL_POINTS} पॉइंट्स  

⚠️ महत्वपूर्ण: बॉट यूज़ करने के लिए पहले ग्रुप जॉइन करना ज़रूरी है।  

आपका ID: {user_id}
"""

    markup = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🚀 Open WebApp", web_app=types.WebAppInfo(WEB_URL))
    invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    invite_btn = types.InlineKeyboardButton("🔗 Invite Friends", url=invite_link)
    markup.add(web_btn, invite_btn)
    bot.send_message(user_id, welcome_text, reply_markup=markup)

    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 प्रोफाइल", "🎁 पॉइंट्स पाओ")
    menu.row("💰 Wallet", "📤 Submit URL")
    bot.send_message(user_id, "👇 नीचे दिए गए बटन से आगे बढ़ें:", reply_markup=menu)

# ===== Menu Handler =====
@bot.message_handler(func=lambda msg: True)
def handle_all(message):
    user_id = message.from_user.id
    check_user(user_id)
    text = message.text

    if text == "📊 प्रोफाइल":
        cur.execute("SELECT points, daily_points FROM users WHERE user_id=?", (user_id,))
        points, dpoints = cur.fetchone()
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.reply_to(message, f"👤 आपके पॉइंट्स: {points}\n📅 आज आपने {dpoints}/{DAILY_POINT_LIMIT} पॉइंट्स कमाए।\n\n🔗 आपका Referral Link:\n{ref_link}")

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
            bot.reply_to(message, "⚠️ आज की पॉइंट्स लिमिट पूरी हो गई है। कल फिर कोशिश करें!")

    elif text == "💰 Wallet":
        cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cur.fetchone()[0]
        bot.reply_to(message, f"💵 आपके Wallet में पॉइंट्स: {points}")

    elif text == "📤 Submit URL":
        cur.execute("SELECT points, url_submitted FROM users WHERE user_id=?", (user_id,))
        points, url_submitted = cur.fetchone()
        if points < 1280:
            bot.send_message(user_id, "⚠️ आपके Wallet में कम पॉइंट्स हैं। 1280 पॉइंट्स होने पर ही URL submit कर सकते हैं।")
        elif url_submitted:
            bot.send_message(user_id, "⚠️ आपने पहले ही URL submit किया है।")
        else:
            msg = bot.send_message(user_id, "📌 कृपया अपना YouTube URL भेजें (1280 Coin deduct होंगे):")
            bot.register_next_step_handler(msg, process_url)

    elif text == "👑 Admin":
        if user_id == ADMIN_ID:
            bot.reply_to(message, "✅ आप Admin हैं!")
        else:
            bot.reply_to(message, "⛔ यह फीचर सिर्फ़ Admin के लिए है।")

# ===== Process URL =====
def process_url(message):
    user_id = message.from_user.id
    url = message.text.strip()

    if "youtube.com" in url or "youtu.be" in url:
        cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cur.fetchone()[0]
        if points < 1280:
            bot.reply_to(message, "⚠️ आपके Wallet में अब 1280 पॉइंट्स नहीं हैं। URL submit failed।")
            return
        new_points = points - 1280
        cur.execute("UPDATE users SET points=?, url_submitted=1 WHERE user_id=?", (new_points, user_id))
        conn.commit()
        bot.send_message(ADMIN_ID, f"🎯 User {user_id} ने URL submit किया:\n{url}\n💵 1280 Coin deduct हो गए।")
        bot.reply_to(message, f"✅ आपका URL submit हो गया और 1280 Coin Wallet से deduct हो गए।\n💵 अब आपके पास {new_points} Coin हैं।")
    else:
        bot.reply_to(message, "⚠️ सही YouTube URL भेजें। फिर से कोशिश करें।")

# ===== Run Bot =====
bot.infinity_polling(timeout=10, long_polling_timeout=5)