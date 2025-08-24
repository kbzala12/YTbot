import telebot, sqlite3
from telebot import types
from config import *
from keep_alive import keep_alive

# ========== KEEP ALIVE ==========
keep_alive()

# ========== DB SETUP ==========
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    points INTEGER DEFAULT 0,
    videos INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    ref INTEGER DEFAULT 0,
    referred_by TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS redemptions (
    id TEXT,
    code TEXT,
    UNIQUE(id, code)
)
""")
conn.commit()

# ========== FUNCTIONS ==========
def check_user(user_id):
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    return {"id": row[0], "points": row[1], "videos": row[2], "shares": row[3], "ref": row[4], "referred_by": row[5]} if row else None

def add_points(user_id, field, max_limit, increment, points):
    cursor.execute(f"SELECT {field}, points FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row and row[0] < max_limit:
        cursor.execute(f"UPDATE users SET {field} = {field} + ?, points = points + ? WHERE id = ?", (increment, points, user_id))
        conn.commit()
        return True
    return False

def apply_referral(new_user_id, ref_id):
    if new_user_id == ref_id: return
    user = get_user(new_user_id)
    if user["referred_by"]: return
    if get_user(ref_id):
        cursor.execute("UPDATE users SET ref = ref + 1, points = points + 50 WHERE id = ?", (ref_id,))
        cursor.execute("UPDATE users SET referred_by = ? WHERE id = ?", (ref_id, new_user_id))
        conn.commit()

# ========== TELEGRAM BOT ==========
bot = telebot.TeleBot(BOT_TOKEN)

def is_user_in_channel(user_id):
    try:
        member = bot.get_chat_member(TELEGRAM_GROUP, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error: {e}")
        return False

def main_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("🎥 वीडियो देखा", "📤 शेयर किया")
    menu.row("📊 मेरी जानकारी", "🔗 रेफरल लिंक")
    menu.row("🎯 प्रमोशन सबमिट")
    return menu

@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)

    if not is_user_in_channel(user_id):
        join_btn = types.InlineKeyboardMarkup()
        join_btn.add(types.InlineKeyboardButton("📥 ग्रुप जॉइन करें", url=f"https://t.me/{TELEGRAM_GROUP.replace('@', '')}"))
        bot.send_message(message.chat.id, "🚫 पहले हमारे Telegram Group को जॉइन करें:", reply_markup=join_btn)
        return

    check_user(user_id)

    if len(message.text.split()) > 1:
        ref_id = message.text.split()[1]
        apply_referral(user_id, ref_id)

    bot.send_message(message.chat.id,
        f"👋 BoomUp Bot में आपका स्वागत है!\n\n🎥 Video = 10 pts\n📤 Share = 25 pts\n🔗 Referral = 50 pts\n🎯 Promotion = 1000 pts\n\n📺 {YOUTUBE_CHANNEL}\n💬 {TELEGRAM_GROUP}",
        reply_markup=main_menu())

@bot.message_handler(func=lambda msg: True)
def handle_all(message):
    user_id = str(message.from_user.id)
    check_user(user_id)
    text = message.text

    if text == "🎥 वीडियो देखा":
        msg = "🎥 इन वीडियो को देखो और अंत में दिए गए कोड को भेजो:\n\n"
        for code, link in VIDEO_CODES.items():
            msg += f"🔗 {link}\n"
        msg += "\n🔑 कोड मिलने पर मुझे भेजो (जैसे: boom123)"
        bot.reply_to(message, msg)

    elif text == "📤 शेयर किया":
        if add_points(user_id, "shares", 5, 1, 25):
            bot.reply_to(message, "✅ शेयर करने के लिए धन्यवाद, +25 पॉइंट्स!")
        else:
            bot.reply_to(message, "❌ आपने 5 शेयर की लिमिट पूरी कर ली है।")

    elif text == "📊 मेरी जानकारी":
        u = get_user(user_id)
        bot.reply_to(message, f"""📊 आपकी जानकारी:
Total Points: {u['points']}
🎥 Videos: {u['videos']}/10
📤 Shares: {u['shares']}/5
🔗 Referrals: {u['ref']}""")

    elif text == "🔗 रेफरल लिंक":
        bot.reply_to(message, f"🔗 आपका रेफरल लिंक:\nhttps://t.me/Hkzyt_bot?start={user_id}")

    elif text == "🎯 प्रमोशन सबमिट":
        u = get_user(user_id)
        if u['points'] >= 1000:
            bot.reply_to(message, "✅ कृपया अपना प्रमोशन लिंक भेजें:")
        else:
            bot.reply_to(message, "❌ प्रमोशन के लिए 1000 पॉइंट्स ज़रूरी हैं।")

@bot.message_handler(func=lambda m: m.text.lower() in VIDEO_CODES)
def handle_secret_code(message):
    user_id = str(message.from_user.id)
    code = message.text.lower()

    cursor.execute("SELECT id FROM redemptions WHERE id = ? AND code = ?", (user_id, code))
    if cursor.fetchone():
        bot.reply_to(message, "⚠️ आपने ये कोड पहले ही इस्तेमाल किया है।")
        return

    if add_points(user_id, "videos", 10, 1, 10):
        cursor.execute("INSERT INTO redemptions (id, code) VALUES (?, ?)", (user_id, code))
        conn.commit()
        bot.reply_to(message, "✅ सही कोड! आपको 10 पॉइंट्स मिले 🎉")
    else:
        bot.reply_to(message, "⚠️ आपने पहले ही 10 वीडियो पूरे कर लिए हैं।")

@bot.message_handler(content_types=['text'])
def promotion_handler(message):
    user_id = str(message.from_user.id)
    u = get_user(user_id)
    if u and u['points'] >= 1000 and message.text.startswith("http"):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve:{user_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject:{user_id}")
        )
        bot.send_message(ADMIN_ID, f"📣 User {user_id} sent a promo:\n{message.text}", reply_markup=markup)
        bot.reply_to(message, "📤 आपका लिंक भेज दिया गया है। 12 घंटे में रिव्यू होगा।")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    action, user_id = call.data.split(":")
    if action == "approve":
        bot.send_message(user_id, "✅ आपका लिंक अप्रूव हो गया है! 3 दिन तक लाइव रहेगा.")
    elif action == "reject":
        bot.send_message(user_id, "❌ आपका प्रमोशन लिंक reject कर दिया गया है.")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

print("🤖 Bot is running...")
bot.infinity_polling()