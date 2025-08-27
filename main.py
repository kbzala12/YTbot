import telebot
from telebot import types
import sqlite3
from config import *
from keep_alive import keep_alive

# ✅ Bot initialize
bot = telebot.TeleBot(BOT_TOKEN)

# ✅ Database setup
def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 0,
                referrals INTEGER DEFAULT 0
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT,
                status TEXT DEFAULT 'pending'
                )""")
    conn.commit()
    conn.close()

init_db()

# ✅ Add user if not exists
def add_user(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, coins, referrals) VALUES (?, ?, ?)", (user_id, 50, 0))  # बोनस 50 कॉइन
    conn.commit()
    conn.close()

# ✅ Get coins
def get_coins(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# ✅ Update coins
def update_coins(user_id, coins):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET coins=? WHERE user_id=?", (coins, user_id))
    conn.commit()
    conn.close()

# ✅ Start Command (with referral)
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    args = message.text.split()

    add_user(user_id)

    # Referral सिस्टम
    if len(args) > 1:
        ref_id = int(args[1])
        if ref_id != user_id:
            conn = sqlite3.connect("bot.db")
            c = conn.cursor()
            c.execute("UPDATE users SET coins = coins + 100, referrals = referrals + 1 WHERE user_id=?", (ref_id,))
            conn.commit()
            conn.close()
            bot.send_message(ref_id, f"🎉 आपको रेफ़रल से 100 कॉइन मिले! {message.from_user.first_name} ने आपका लिंक जॉइन किया।")

    keyboard = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🌐 Open WebApp", url=WEB_URL)
    join_btn = types.InlineKeyboardButton("📢 Join Group", url="https://t.me/boomupbot10")
    keyboard.add(web_btn)
    keyboard.add(join_btn)

    bot.send_message(
        user_id,
        f"👋 स्वागत है {message.from_user.first_name}!\n\n"
        f"👉 आपका बैलेंस: {get_coins(user_id)} कॉइन\n\n"
        "👇 नीचे दिए गए बटन से WebApp खोलें और Group Join करें।",
        reply_markup=keyboard
    )

# ✅ Balance check
@bot.message_handler(commands=['balance'])
def balance(message):
    coins = get_coins(message.chat.id)
    bot.send_message(message.chat.id, f"💰 आपके पास {coins} कॉइन हैं।")

# ✅ Submit URL
@bot.message_handler(commands=['submit'])
def submit(message):
    user_id = message.chat.id
    coins = get_coins(user_id)

    if coins < 1280:
        bot.send_message(user_id, "❌ आपके पास पर्याप्त कॉइन नहीं हैं (1280 की ज़रूरत है)।")
        return

    msg = bot.send_message(user_id, "🔗 कृपया अपना YouTube URL भेजें:")
    bot.register_next_step_handler(msg, process_url)

def process_url(message):
    user_id = message.chat.id
    url = message.text
    coins = get_coins(user_id)

    if coins >= 1280:
        update_coins(user_id, coins - 1280)
        conn = sqlite3.connect("bot.db")
        c = conn.cursor()
        c.execute("INSERT INTO submissions (user_id, url, status) VALUES (?, ?, ?)", (user_id, url, "pending"))
        conn.commit()
        conn.close()
        bot.send_message(user_id, "✅ आपका URL सबमिट हो गया है और एडमिन की अप्रूवल का इंतज़ार है।")
        bot.send_message(ADMIN_ID, f"🔔 नया सबमिशन आया है:\n👤 User: {user_id}\n🔗 URL: {url}")
    else:
        bot.send_message(user_id, "❌ आपके पास पर्याप्त कॉइन नहीं हैं।")

# ✅ Admin Panel
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if str(message.chat.id) == str(ADMIN_ID):
        bot.send_message(message.chat.id, "⚙️ Admin Panel:\n\n/approve <id> - सबमिशन अप्रूव करें\n/reject <id> - सबमिशन रिजेक्ट करें")
    else:
        bot.send_message(message.chat.id, "❌ यह कमांड सिर्फ Admin के लिए है।")

# ✅ Approve submission
@bot.message_handler(commands=['approve'])
def approve(message):
    if str(message.chat.id) != str(ADMIN_ID):
        return

    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ सबमिशन ID दीजिए।")
        return

    sub_id = int(args[1])
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE submissions SET status='approved' WHERE id=?", (sub_id,))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"✅ सबमिशन #{sub_id} अप्रूव हो गया।")

# ✅ Reject submission
@bot.message_handler(commands=['reject'])
def reject(message):
    if str(message.chat.id) != str(ADMIN_ID):
        return

    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ सबमिशन ID दीजिए।")
        return

    sub_id = int(args[1])
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE submissions SET status='rejected' WHERE id=?", (sub_id,))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"❌ सबमिशन #{sub_id} रिजेक्ट हो गया।")

# ✅ Run bot
keep_alive()
bot.polling(non_stop=True)