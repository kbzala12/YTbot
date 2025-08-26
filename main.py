import telebot, sqlite3, os
from telebot import types
from datetime import datetime, timedelta

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7978191312:AAFFaOkxBSI9YoN4uR3I5FtZbfQNojT8F4U")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7459795138))
WEB_URL = os.environ.get("WEB_URL", "https://studiokbyt.onrender.com/")
COMMUNITY_LINK = os.environ.get("COMMUNITY_LINK", "https://t.me/boomupbot10")

REF_POINTS = 100      # रेफरल कॉइन
DAILY_BONUS = 30      # डेली बोनस

bot = telebot.TeleBot(BOT_TOKEN)

# ========== DATABASE ==========
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0,
    referred_by INTEGER,
    last_bonus TEXT
)
""")
conn.commit()

# ========== MAIN KEYBOARD ==========
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎁 Wallet", "📤 Submit URL")
    kb.row("👥 Invite", "🎉 Daily Bonus")
    kb.row("🌐 Join Community")
    return kb

# ========== ADMIN KEYBOARD ==========
def admin_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 Total Users", "💰 Total Coins")
    kb.row("⬅️ Back")
    return kb

# ========== START ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    name = message.from_user.first_name

    # नया यूज़र DB में
    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        ref = None
        if len(message.text.split()) > 1:
            try:
                ref = int(message.text.split()[1])
                if ref != user_id:
                    cursor.execute("UPDATE users SET points = points + ? WHERE id=?", (REF_POINTS, ref))
            except:
                pass
        cursor.execute("INSERT INTO users (id, name, points, referred_by) VALUES (?, ?, ?, ?)",
                       (user_id, name, 0, ref))
        conn.commit()
        if ref:
            bot.send_message(ref, f"🎉 नया यूज़र जुड़ा! आपको {REF_POINTS} कॉइन मिले ✅")

    # Welcome Message
    welcome_text = (
        "🎬 *Video Coin Earner Bot में आपका स्वागत है!* 🎬\n\n"
        f"नमस्ते {name}! 👋\n\n"
        "📹 वीडियो देखो, कॉइन कमाओ और  \n"
        "💰 अपना YouTube चैनल मोनेटाइजेशन करवाओ ✅\n\n"
        f"📌 कमाई नियम:\n• प्रत्येक वीडियो = 30 पॉइंट्स\n• दैनिक बोनस = {DAILY_BONUS} पॉइंट्स\n• रेफरल = {REF_POINTS} पॉइंट्स\n\n"
        "⚠️ बॉट यूज़ करने के लिए पहले कम्युनिटी जॉइन करें।"
    )

    # Inline buttons: Open App + Join Community + Invite
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎬 Open App", url=WEB_URL))
    markup.add(types.InlineKeyboardButton("📢 Join Community", url=COMMUNITY_LINK))
    markup.add(types.InlineKeyboardButton("👥 Invite Friend", switch_inline_query=""))

    bot.send_message(user_id, welcome_text, parse_mode="Markdown", reply_markup=markup)
    bot.send_message(user_id, "👇 नीचे मेन मेन्यू:", reply_markup=main_keyboard())

# ========== WALLET ==========
@bot.message_handler(func=lambda m: m.text == "🎁 Wallet")
def wallet(message):
    user_id = message.chat.id
    cursor.execute("SELECT points FROM users WHERE id=?", (user_id,))
    points = cursor.fetchone()[0]
    bot.send_message(user_id, f"👤 *आपका प्रोफाइल*\n\n🆔 ID: {user_id}\n💰 Wallet Balance: {points} कॉइन",
                     parse_mode="Markdown")

# ========== SUBMIT URL ==========
@bot.message_handler(func=lambda m: m.text == "📤 Submit URL")
def submit_url(message):
    bot.send_message(message.chat.id, f"🔗 अपना लिंक यहां सबमिट करें: \n{WEB_URL}")

# ========== INVITE ==========
@bot.message_handler(func=lambda m: m.text == "👥 Invite")
def invite(message):
    user_id = message.chat.id
    bot.send_message(user_id,
                     f"👥 दोस्तों को इनवाइट करें और हर नए यूज़र पर {REF_POINTS} पॉइंट्स कमाएँ!\n\n"
                     f"👉 आपका लिंक:\nhttps://t.me/{bot.get_me().username}?start={user_id}")

# ========== DAILY BONUS ==========
@bot.message_handler(func=lambda m: m.text == "🎉 Daily Bonus")
def daily_bonus(message):
    user_id = message.chat.id
    cursor.execute("SELECT last_bonus FROM users WHERE id=?", (user_id,))
    last_bonus = cursor.fetchone()[0]
    now = datetime.now()
    if not last_bonus or (now - datetime.fromisoformat(last_bonus)) > timedelta(hours=24):
        cursor.execute("UPDATE users SET points = points + ?, last_bonus=? WHERE id=?",
                       (DAILY_BONUS, now.isoformat(), user_id))
        conn.commit()
        bot.send_message(user_id, f"🎉 आपको {DAILY_BONUS} कॉइन का डेली बोनस मिल गया ✅")
    else:
        bot.send_message(user_id, "❌ आपने आज का बोनस पहले ही ले लिया है। कल फिर आएं!")

# ========== JOIN COMMUNITY ==========
@bot.message_handler(func=lambda m: m.text == "🌐 Join Community")
def join(message):
    bot.send_message(message.chat.id, f"🌐 हमारी कम्युनिटी जॉइन करें:\n👉 {COMMUNITY_LINK}")

# ========== ADMIN PANEL ==========
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "🔐 Admin Panel Opened", reply_markup=admin_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ यह फीचर केवल एडमिन के लिए है।")

@bot.message_handler(func=lambda m: m.text == "📊 Total Users")
def total_users(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        bot.send_message(ADMIN_ID, f"👥 Total Registered Users: {total}")

@bot.message_handler(func=lambda m: m.text == "💰 Total Coins")
def total_coins(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute("SELECT SUM(points) FROM users")
        total = cursor.fetchone()[0]
        bot.send_message(ADMIN_ID, f"💰 Total Distributed Coins: {total}")

@bot.message_handler(func=lambda m: m.text == "⬅️ Back")
def back(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "⬅️ Main Menu", reply_markup=main_keyboard())

# ========== RUN BOT ==========
print("🤖 Bot Started...")
bot.infinity_polling()