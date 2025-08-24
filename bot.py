import telebot
from telebot import types
import sqlite3
import datetime
from config import BOT_TOKEN, ADMIN_ID, WEB_URL, VIP_YT_CHANNEL

bot = telebot.TeleBot(BOT_TOKEN)

# 🎥 Config
DAILY_POINT_LIMIT = 100
VIDEO_POINTS = 30
REFERRAL_POINTS = 100   # हर नए यूज़र पर 100 कॉइन
LINK_SUBMIT_COST = 1280 # URL Submit Cost
SUBSCRIBE_POINTS = 10   # Subscribe करने पर मिलने वाले पॉइंट्स
BOT_USERNAME = "Bingyt_bot"

# 📂 Database Setup
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0,
        video_count INTEGER DEFAULT 0,
        daily_points INTEGER DEFAULT 0,
        last_active TEXT,
        ref_id INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

# 📌 User check & create
def check_user(user_id, ref_id=None):
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()

    today = datetime.date.today().isoformat()

    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cur.fetchone()

    if not user:
        cur.execute("INSERT INTO users (user_id, points, video_count, daily_points, last_active, ref_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, 0, 0, 0, today, ref_id))
        conn.commit()

        # Referral system
        if ref_id and ref_id != user_id:
            cur.execute("UPDATE users SET points = points + ?, daily_points = daily_points + ? WHERE user_id=?",
                        (REFERRAL_POINTS, REFERRAL_POINTS, ref_id))
            conn.commit()
            bot.send_message(ref_id, f"🎉 आपके referral से नया यूज़र जुड़ा! आपको {REFERRAL_POINTS} कॉइन मिले।")

    else:
        # अगर नया दिन है तो reset करो
        last_active = user[4]
        if last_active != today:
            cur.execute("UPDATE users SET daily_points=?, last_active=? WHERE user_id=?", (0, today, user_id))
            conn.commit()

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
• प्रत्येक वीडियो = {VIDEO_POINTS} कॉइन  
• Subscribe = {SUBSCRIBE_POINTS} कॉइन  
• दैनिक लिमिट = {DAILY_POINT_LIMIT} कॉइन  
• URL Submit करने की लागत = {LINK_SUBMIT_COST} कॉइन  

👥 रेफरल सिस्टम:  
• दोस्तों को इनवाइट करें  
• हर नए यूज़र पर {REFERRAL_POINTS} कॉइन  

⚠️ महत्वपूर्ण: बॉट यूज़ करने के लिए पहले ग्रुप जॉइन करना ज़रूरी है।  

आपका ID: {user_id}
"""

    markup = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🚀 Open WebApp", web_app=types.WebAppInfo(WEB_URL))
    invite_btn = types.InlineKeyboardButton("🔗 Invite Friends", url=f"https://t.me/{BOT_USERNAME}?start={user_id}")
    markup.add(web_btn, invite_btn)

    bot.send_message(user_id, welcome_text, reply_markup=markup)

    # ✅ Main Menu with Subscribe button
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 प्रोफाइल", "🎁 पॉइंट्स पाओ")
    menu.row("💰 Wallet", "🔗 Invite Friends")
    menu.row("📢 Subscribe", "📤 URL Submit")
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
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.reply_to(message, f"👤 आपके पॉइंट्स: {points}\n📅 आज आपने {dpoints}/{DAILY_POINT_LIMIT} कमाए।\n\n🔗 Referral Link:\n{ref_link}")

    elif text == "🎁 पॉइंट्स पाओ":
        cur.execute("SELECT points, daily_points, last_active FROM users WHERE user_id=?", (user_id,))
        points, dpoints, last_active = cur.fetchone()

        today = datetime.date.today().isoformat()
        if last_active != today:
            dpoints = 0
            cur.execute("UPDATE users SET daily_points=?, last_active=? WHERE user_id=?", (0, today, user_id))
            conn.commit()

        if dpoints + VIDEO_POINTS <= DAILY_POINT_LIMIT:
            new_points = points + VIDEO_POINTS
            new_dpoints = dpoints + VIDEO_POINTS
            cur.execute("UPDATE users SET points=?, daily_points=?, last_active=? WHERE user_id=?", 
                        (new_points, new_dpoints, today, user_id))
            conn.commit()
            bot.reply_to(message, f"✅ आपको {VIDEO_POINTS} कॉइन मिले! (आज {new_dpoints}/{DAILY_POINT_LIMIT})")
        else:
            bot.reply_to(message, "⚠️ आज की कॉइन लिमिट पूरी हो गई है। कल फिर कोशिश करें!")

    elif text == "💰 Wallet":
        cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cur.fetchone()[0]
        bot.reply_to(message, f"💵 आपके Wallet में कॉइन: {points}")

    elif text == "🔗 Invite Friends":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.reply_to(message, f"👥 अपने दोस्तों को इनवाइट करें!\n\n🔗 आपका Referral Link:\n{ref_link}\n\nहर नए यूज़र पर आपको {REFERRAL_POINTS} कॉइन मिलेंगे ✅")

    elif text == "📤 URL Submit":
        cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cur.fetchone()[0]

        if points >= LINK_SUBMIT_COST:
            bot.reply_to(message, "📌 कृपया वह YouTube URL भेजें जिसे आप सबमिट करना चाहते हैं।")
            bot.register_next_step_handler(message, process_url_submit)
        else:
            bot.reply_to(message, f"⚠️ आपके पास पर्याप्त कॉइन नहीं हैं!\nआपको {LINK_SUBMIT_COST} कॉइन चाहिए।")

    elif text == "📢 Subscribe":
        markup = types.InlineKeyboardMarkup()
        sub_btn = types.InlineKeyboardButton("📺 चैनल Subscribe करें", url=VIP_YT_CHANNEL)
        done_btn = types.InlineKeyboardButton("✅ Subscribed", callback_data="sub_done")
        markup.add(sub_btn)
        markup.add(done_btn)
        bot.send_message(user_id, "👉 हमारे VIP YouTube चैनल को Subscribe करें और 10 कॉइन पाएं:", reply_markup=markup)

    elif text == "👑 Admin":
        if user_id == ADMIN_ID:
            bot.reply_to(message, "✅ आप Admin हैं!")
        else:
            bot.reply_to(message, "⛔ यह फीचर सिर्फ़ Admin के लिए है।")

    conn.close()


# 🎯 Process URL Submit
def process_url_submit(message):
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

        bot.send_message(user_id, f"✅ आपका URL सबमिट हो गया!\nआपके {LINK_SUBMIT_COST} कॉइन कटे।")
        # Admin को भेजो
        bot.send_message(ADMIN_ID, f"📩 New URL Submission:\n👤 User ID: {user_id}\n🔗 URL: {url}")
    else:
        bot.send_message(user_id, "⚠️ आपके पास पर्याप्त कॉइन नहीं हैं।")

    conn.close()


# 🎯 Callback Handler (Subscribe Done)
@bot.callback_query_handler(func=lambda call: call.data == "sub_done")
def sub_done(call):
    user_id = call.from_user.id
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()

    cur.execute("SELECT points, daily_points, last_active FROM users WHERE user_id=?", (user_id,))
    points, dpoints, last_active = cur.fetchone()

    today = datetime.date.today().isoformat()
    if last_active != today:
        dpoints = 0
        cur.execute("UPDATE users SET daily_points=?, last_active=? WHERE user_id=?", (0, today, user_id))
        conn.commit()

    if dpoints + SUBSCRIBE_POINTS <= DAILY_POINT_LIMIT:
        new_points = points + SUBSCRIBE_POINTS
        new_dpoints = dpoints + SUBSCRIBE_POINTS
        cur.execute("UPDATE users SET points=?, daily_points=?, last_active=? WHERE user_id=?", 
                    (new_points, new_dpoints, today, user_id))
        conn.commit()
        bot.answer_callback_query(call.id, f"✅ आपको {SUBSCRIBE_POINTS} कॉइन मिले!")
        bot.send_message(user_id, f"🎉 Thank you! आपके Wallet में {SUBSCRIBE_POINTS} कॉइन जुड़ गए ✅")
    else:
        bot.answer_callback_query(call.id, "⚠️ आज की Daily Limit पूरी हो गई है।")

    conn.close()


# ♾ Bot Run
bot.infinity_polling()