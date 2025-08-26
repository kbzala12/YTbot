import telebot, sqlite3
from telebot import types
from datetime import datetime, timedelta
from config import BOT_TOKEN, ADMIN_ID, WEB_URL, COMMUNITY_LINK, REF_POINTS, DAILY_BONUS, LINK_SUBMIT_COST

bot = telebot.TeleBot(BOT_TOKEN)

# ========== Database ==========
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
cursor.execute("""
CREATE TABLE IF NOT EXISTS urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    url TEXT,
    timestamp TEXT
)
""")
conn.commit()

# ========== Keyboards ==========
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎁 Wallet", "📤 Submit URL")
    kb.row("👥 Invite", "🎉 Daily Bonus")
    kb.row("🌐 Join Community")
    return kb

def admin_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 Total Users", "💰 Total Coins")
    kb.row("📄 Submitted URLs", "⬅️ Back")
    return kb

# ========== Start Command ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    name = message.from_user.first_name

    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        ref = None
        if len(message.text.split()) > 1:
            try:
                ref = int(message.text.split()[1])
                if ref != user_id:
                    cursor.execute("UPDATE users SET points = points + ? WHERE id=?", (REF_POINTS, ref))
                    bot.send_message(ref, f"🎉 नया यूज़र जुड़ा! आपको {REF_POINTS} कॉइन मिले ✅")
                    bot.send_message(ADMIN_ID, f"📌 Referral Alert: {name} ने {ref} के लिंक से join किया।")
            except:
                pass
        cursor.execute("INSERT INTO users (id, name, points, referred_by) VALUES (?, ?, ?, ?)",
                       (user_id, name, 0, ref))
        conn.commit()

    welcome_text = (
        f"🎬 *Video Coin Earner Bot में आपका स्वागत है!* 🎬\n\n"
        f"नमस्ते {name}! 👋\n\n"
        f"📌 कमाई नियम:\n• प्रत्येक वीडियो = 30 पॉइंट्स\n• डेली बोनस = {DAILY_BONUS} पॉइंट्स\n• रेफरल = {REF_POINTS} पॉइंट्स\n• URL Submit = {LINK_SUBMIT_COST} पॉइंट्स\n\n"
        "⚠️ बॉट यूज़ करने के लिए पहले कम्युनिटी जॉइन करें।"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎬 Open App", url=WEB_URL))
    markup.add(types.InlineKeyboardButton("📢 Join Community", url=COMMUNITY_LINK))
    markup.add(types.InlineKeyboardButton("👥 Invite Friend", switch_inline_query=""))

    bot.send_message(user_id, welcome_text, parse_mode="Markdown", reply_markup=markup)
    bot.send_message(user_id, "👇 नीचे मेन मेन्यू:", reply_markup=main_keyboard())

# ========== Wallet ==========
@bot.message_handler(func=lambda m: m.text == "🎁 Wallet")
def wallet(message):
    user_id = message.chat.id
    cursor.execute("SELECT points FROM users WHERE id=?", (user_id,))
    points = cursor.fetchone()[0]
    bot.send_message(user_id, f"👤 *आपका प्रोफाइल*\n\n🆔 ID: {user_id}\n💰 Wallet Balance: {points} कॉइन", parse_mode="Markdown")

# ========== Submit URL ==========
@bot.message_handler(func=lambda m: m.text == "📤 Submit URL")
def submit_url(message):
    user_id = message.chat.id
    cursor.execute("SELECT points FROM users WHERE id=?", (user_id,))
    points = cursor.fetchone()[0]
    if points < LINK_SUBMIT_COST:
        bot.send_message(user_id, f"❌ आपको URL submit करने के लिए {LINK_SUBMIT_COST} कॉइन चाहिए। आपका balance: {points} कॉइन")
        return
    msg = bot.send_message(user_id, f"🔗 अपना लिंक भेजें (Cost: {LINK_SUBMIT_COST} कॉइन):")
    bot.register_next_step_handler(msg, save_url)

def save_url(message):
    user_id = message.chat.id
    url = message.text
    cursor.execute("SELECT points FROM users WHERE id=?", (user_id,))
    points = cursor.fetchone()[0]
    if points >= LINK_SUBMIT_COST:
        cursor.execute("UPDATE users SET points = points - ? WHERE id=?", (LINK_SUBMIT_COST, user_id))
        cursor.execute("INSERT INTO urls (user_id, url, timestamp) VALUES (?, ?, ?)", (user_id, url, str(datetime.now())))
        conn.commit()
        bot.send_message(user_id, f"✅ आपका URL submit हो गया और {LINK_SUBMIT_COST} कॉइन deduct हुए।")
        bot.send_message(ADMIN_ID, f"📢 New URL Submitted by {user_id}:\n{url}")
    else:
        bot.send_message(user_id, "❌ आपका balance पर्याप्त नहीं है।")

# ========== Invite ==========
@bot.message_handler(func=lambda m: m.text == "👥 Invite")
def invite(message):
    user_id = message.chat.id
    bot.send_message(user_id, f"👥 दोस्तों को इनवाइट करें और हर नए यूज़र पर {REF_POINTS} पॉइंट्स कमाएँ!\n\n"
                              f"👉 आपका लिंक:\nhttps://t.me/{bot.get_me().username}?start={user_id}")

# ========== Daily Bonus ==========
@bot.message_handler(func=lambda m: m.text == "🎉 Daily Bonus")
def daily_bonus(message):
    user_id = message.chat.id
    cursor.execute("SELECT last_bonus FROM users WHERE id=?", (user_id,))
    last_bonus = cursor.fetchone()[0]
    now = datetime.now()
    if not last_bonus or (now - datetime.fromisoformat(last_bonus)) > timedelta(hours=24):
        cursor.execute("UPDATE users SET points = points + ?, last_bonus=? WHERE id=?", (DAILY_BONUS, now.isoformat(), user_id))
        conn.commit()
        bot.send_message(user_id, f"🎉 आपको {DAILY_BONUS} कॉइन का डेली बोनस मिल गया ✅")
    else:
        bot.send_message(user_id, "❌ आपने आज का बोनस पहले ही ले लिया है। कल फिर आएं!")

# ========== Join Community ==========
@bot.message_handler(func=lambda m: m.text == "🌐 Join Community")
def join(message):
    bot.send_message(message.chat.id, f"🌐 हमारी कम्युनिटी जॉइन करें:\n👉 {COMMUNITY_LINK}")

# ========== Admin Panel ==========
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

@bot.message_handler(func=lambda m: m.text == "📄 Submitted URLs")
def submitted_urls(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute("SELECT user_id, url, timestamp FROM urls ORDER BY id DESC")
        urls = cursor.fetchall()
        if urls:
            for u in urls:
                bot.send_message(ADMIN_ID, f"User: {u[0]}\nURL: {u[1]}\nTime: {u[2]}\n---")
        else:
            bot.send_message(ADMIN_ID, "No URLs submitted yet.")

@bot.message_handler(func=lambda m: m.text == "⬅️ Back")
def back(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "⬅️ Main Menu", reply_markup=main_keyboard())

# ========== Run Bot ==========
print("🤖 Bot Started...")
bot.infinity_polling()