import telebot
from telebot import types
import sqlite3
from config import BOT_TOKEN, ADMIN_ID, WEB_URL

bot = telebot.TeleBot(BOT_TOKEN)

# 🎥 Config
DAILY_POINT_LIMIT = 100
VIDEO_POINTS = 30
REFERRAL_POINTS = 100
BOT_USERNAME = "Bingyt_bot"   # ✅ अब invite लिंक के लिए नया bot username

# 📂 Database Setup
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0,
        video_count INTEGER DEFAULT 0,
        daily_points INTEGER DEFAULT 0,
        ref_id INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

# 📌 User check & create
def check_user(user_id, ref_id=None):
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cur.fetchone()

    if not user:
        initial_points = REFERRAL_POINTS if ref_id else 0
        cur.execute("INSERT INTO users (user_id, points, video_count, daily_points, ref_id) VALUES (?, ?, ?, ?, ?)",
                    (user_id, initial_points, 0, initial_points, ref_id))
        conn.commit()

        # Referrer को points देना
        if ref_id:
            cur.execute("UPDATE users SET points = points + ?, daily_points = daily_points + ? WHERE user_id=?",
                        (REFERRAL_POINTS, REFERRAL_POINTS, ref_id))
            conn.commit()
            bot.send_message(ref_id, f"🎉 आपके referral से नए user ने join किया! आपको {REFERRAL_POINTS} पॉइंट्स मिले।")

    conn.close()

# 🎬 /start Command
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
    # ✅ Invite Link अब Bingyt_bot के साथ
    invite_link = f"https://t.me/Bingyt_bot?start={user_id}"
    invite_btn = types.InlineKeyboardButton("🔗 Invite Friends", url=invite_link)
    markup.add(web_btn, invite_btn)

    bot.send_message(user_id, welcome_text, reply_markup=markup)

    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 प्रोफाइल", "🎁 पॉइंट्स पाओ")
    menu.row("💰 Wallet")
    bot.send_message(user_id, "👇 नीचे दिए गए बटन से आगे बढ़ें:", reply_markup=menu)

# 🔘 Menu Handler
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
        ref_link = f"https://t.me/Bingyt_bot?start={user_id}"  # ✅ Updated referral link
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

    elif text == "👑 Admin":
        if user_id == ADMIN_ID:
            bot.reply_to(message, "✅ आप Admin हैं!")
        else:
            bot.reply_to(message, "⛔ यह फीचर सिर्फ़ Admin के लिए है।")

    conn.close()

# ♾ Bot Run
bot.infinity_polling()