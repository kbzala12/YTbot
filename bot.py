import telebot
from telebot import types
import sqlite3
from config import BOT_TOKEN, ADMIN_ID, WEB_URL

bot = telebot.TeleBot(BOT_TOKEN)

# Config
DAILY_POINT_LIMIT = 100
VIDEO_POINTS = 30
REFERRAL_POINTS = 100
BOT_USERNAME = "Bingyt_bot"
LINK_SUBMIT_COST = 1200  # Coin per YouTube URL submission

# Database setup
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
    cur.execute('''CREATE TABLE IF NOT EXISTS submitted_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        url TEXT,
        status TEXT DEFAULT 'pending',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

# User check
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
        if ref_id:
            cur.execute("UPDATE users SET points = points + ?, daily_points = daily_points + ? WHERE user_id=?",
                        (REFERRAL_POINTS, REFERRAL_POINTS, ref_id))
            conn.commit()
            bot.send_message(ref_id, f"🎉 आपके referral से नए user ने join किया! आपको {REFERRAL_POINTS} पॉइंट्स मिले।")
    conn.close()

# /start command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    check_user(user_id, ref_id)

    welcome_text = f"""
🎬 Video Coin Earner Bot में आपका स्वागत है! 🎬

नमस्ते {message.from_user.first_name}!

📹 वीडियो देखो, कॉइन कमाओ और  
💰 YouTube link submit करो ✅  

📌 कमाई नियम:
• प्रत्येक वीडियो = {VIDEO_POINTS} पॉइंट्स  
• दैनिक लिमिट = {DAILY_POINT_LIMIT} पॉइंट्स  
• लिंक submit cost = {LINK_SUBMIT_COST} Coin  

👥 रेफरल सिस्टम:  
• दोस्तों को इनवाइट करें  
• हर नए यूज़र पर {REFERRAL_POINTS} पॉइंट्स  

⚠️ महत्वपूर्ण: बॉट यूज़ करने के लिए पहले ग्रुप जॉइन करना ज़रूरी है।  

आपका ID: {user_id}
"""

    markup = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🚀 Open WebApp", web_app=types.WebAppInfo(WEB_URL))
    markup.add(web_btn)

    bot.send_message(user_id, welcome_text, reply_markup=markup)

    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 प्रोफाइल", "🎁 पॉइंट्स पाओ")
    menu.row("💰 Wallet", "🔗 Invite Friends")
    menu.row("💻 Submit YouTube Link")
    bot.send_message(user_id, "👇 नीचे दिए गए बटन से आगे बढ़ें:", reply_markup=menu)

# Handle messages
@bot.message_handler(func=lambda msg: True)
def handle_all(message):
    user_id = message.from_user.id
    check_user(user_id)
    text = message.text
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()

    if text == "📊 प्रोफाइल":
        cur.execute("SELECT points, daily_points FROM users WHERE user_id=?", (user_id,))
        result = cur.fetchone() or (0,0)
        points, dpoints = result
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.reply_to(message, f"👤 आपके पॉइंट्स: {points}\n📅 आज आपने {dpoints}/{DAILY_POINT_LIMIT} पॉइंट्स कमाए।\n\n🔗 आपका Referral Link:\n{ref_link}")

    elif text == "🎁 पॉइंट्स पाओ":
        cur.execute("SELECT points, daily_points FROM users WHERE user_id=?", (user_id,))
        result = cur.fetchone() or (0,0)
        points, dpoints = result
        if dpoints + VIDEO_POINTS <= DAILY_POINT_LIMIT:
            cur.execute("UPDATE users SET points=?, daily_points=? WHERE user_id=?",
                        (points + VIDEO_POINTS, dpoints + VIDEO_POINTS, user_id))
            conn.commit()
            bot.reply_to(message, f"✅ आपको {VIDEO_POINTS} पॉइंट्स मिले! (आज {dpoints + VIDEO_POINTS}/{DAILY_POINT_LIMIT})")
        else:
            bot.reply_to(message, "⚠️ आज की पॉइंट्स लिमिट पूरी हो गई है। कल फिर कोशिश करें!")

    elif text == "💰 Wallet":
        cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        result = cur.fetchone()
        points = result[0] if result else 0
        bot.reply_to(message, f"💵 आपके Wallet में पॉइंट्स: {points}")

    elif text == "🔗 Invite Friends":
        invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.reply_to(message, f"अपने दोस्तों को invite करें और {REFERRAL_POINTS} पॉइंट्स पाएं:\n{invite_link}")

    elif text == "💻 Submit YouTube Link":
        bot.send_message(user_id, "अपना YouTube link भेजें। 1200 Coin कटेंगे।")
        bot.register_next_step_handler(message, handle_link_submission)

    elif text == "👑 Admin":
        if user_id == ADMIN_ID:
            bot.send_message(user_id, "✅ आप Admin हैं।\nCommands:\n/links - सभी pending links देखें")
        else:
            bot.send_message(user_id, "⛔ यह फीचर सिर्फ़ Admin के लिए है।")

    conn.close()

# Handle link submission
def handle_link_submission(message):
    user_id = message.from_user.id
    url = message.text.strip()
    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()

    # Check if user has enough points
    cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    result = cur.fetchone()
    points = result[0] if result else 0
    if points < LINK_SUBMIT_COST:
        bot.reply_to(message, f"⚠️ आपके पास पर्याप्त Coin नहीं हैं। {LINK_SUBMIT_COST} Coin चाहिए।")
        conn.close()
        return

    # Deduct points
    cur.execute("UPDATE users SET points = points - ? WHERE user_id=?", (LINK_SUBMIT_COST, user_id))
    # Insert link into submitted_links
    cur.execute("INSERT INTO submitted_links (user_id, url) VALUES (?, ?)", (user_id, url))
    conn.commit()
    conn.close()

    bot.reply_to(message, f"✅ आपका link submit हो गया है! {LINK_SUBMIT_COST} Coin कट गए। Admin approval का इंतजार करें।")
    bot.send_message(ADMIN_ID, f"🆕 नया YouTube link submit हुआ:\nUser: {user_id}\nURL: {url}\n💰 {LINK_SUBMIT_COST} Coin deducted")

# Admin command to view pending links
@bot.message_handler(commands=['links'])
def admin_links(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ यह Admin के लिए है।")
        return

    conn = sqlite3.connect("bot_data.db")
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, url, status FROM submitted_links WHERE status='pending'")
    links = cur.fetchall()
    if not links:
        bot.reply_to(message, "🎉 कोई pending link नहीं है।")
    else:
        text = "⏳ Pending links:\n\n"
        for link in links:
            text += f"ID: {link[0]}\nUser: {link[1]}\nURL: {link[2]}\nStatus: {link[3]}\n\n"
        bot.reply_to(message, text)
    conn.close()

bot.infinity_polling()