import telebot, sqlite3, os

BOT_TOKEN = "8192810260:AAFfhjDfNywZIzkrlVmtAuKFL5_E-ZnsOmU"
bot = telebot.TeleBot(BOT_TOKEN)
DB_PATH = "database.db"

# 📦 DB SETUP
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0)''')
conn.commit()

# 👋 START
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    cur.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()

    photo = open("static/banner.jpg", 'rb')
    bot.send_photo(user_id, photo, caption="""
🎁 *स्वागत है!*
आप इस बॉट से वीडियो देखकर, शेयर करके और रेफ़र करके पॉइंट्स कमा सकते हैं।

🎥 /watch - वीडियो देखें
🔗 /share - शेयर करें
👥 /refer - रेफ़रल लिंक
💰 /points - अपने पॉइंट्स देखें
    """, parse_mode="Markdown")

# 📺 वीडियो देखना
@bot.message_handler(commands=['watch'])
def watch_video(message):
    user_id = message.chat.id
    cur.execute("UPDATE users SET points = points + 10 WHERE id = ?", (user_id,))
    conn.commit()
    bot.reply_to(message, "✅ आपने वीडियो देखा! +10 पॉइंट्स मिले।")

# 🔗 शेयर करना
@bot.message_handler(commands=['share'])
def share_video(message):
    user_id = message.chat.id
    cur.execute("UPDATE users SET points = points + 25 WHERE id = ?", (user_id,))
    conn.commit()
    bot.reply_to(message, "✅ शेयर करने पर +25 पॉइंट्स मिले।")

# 🔁 रेफ़र सिस्टम
@bot.message_handler(commands=['refer'])
def refer_system(message):
    user_id = message.chat.id
    link = f"https://t.me/Hkzyt_bot?start={user_id}"
    bot.reply_to(message, f"👥 अपना रेफ़रल लिंक:\n{link}")

# 💰 पॉइंट्स चेक करना
@bot.message_handler(commands=['points'])
def check_points(message):
    user_id = message.chat.id
    cur.execute("SELECT points FROM users WHERE id = ?", (user_id,))
    result = cur.fetchone()
    points = result[0] if result else 0
    bot.reply_to(message, f"💰 आपके कुल पॉइंट्स: {points}")

bot.polling()
