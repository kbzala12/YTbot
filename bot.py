import telebot
import json
from config import BOT_TOKEN, ADMIN_ID, YOUTUBE_CHANNEL, TELEGRAM_GROUP, WEB_URL

bot = telebot.TeleBot(BOT_TOKEN)
data_file = "data.json"

# ---------------- Database ----------------
def load_data():
    try:
        with open(data_file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f)

users = load_data()

def check_user(user_id):
    if str(user_id) not in users:
        users[str(user_id)] = {"points": 0, "videos": 0, "shares": 0, "ref": 0}
        save_data(users)

# ---------------- Config ----------------
REFERRAL_POINTS = 100
VIDEO_POINTS = 10
SHARE_POINTS = 25
VIDEO_LIMIT = 10
SHARE_LIMIT = 5

# ---------------- Start ----------------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    check_user(user_id)

    # Referral Check
    if len(args) > 1:
        referrer_id = args[1]
        if referrer_id != user_id:
            check_user(referrer_id)
            users[referrer_id]["points"] += REFERRAL_POINTS
            users[referrer_id]["ref"] += 1
            save_data(users)
            bot.send_message(referrer_id, f"🎉 नया यूज़र आपके लिंक से जुड़ा! आपको {REFERRAL_POINTS} कॉइन मिले ✅")

    # 🌐 Web Button + Invite Button
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🌐 Web Open", url=WEB_URL),
        telebot.types.InlineKeyboardButton("👥 Invite", url=f"https://t.me/YOUR_BOT_USERNAME?start={user_id}")
    )

    # 👋 Welcome SMS
    bot.send_message(message.chat.id,
        f"👋 स्वागत है *BoomUp Bot* में, {message.from_user.first_name}!\n\n"
        f"🎬 वीडियो देखो → {VIDEO_POINTS} कॉइन\n"
        f"🔄 शेयर करो → {SHARE_POINTS} कॉइन\n"
        f"👥 Invite करो → {REFERRAL_POINTS} कॉइन\n\n"
        f"📺 YouTube: {YOUTUBE_CHANNEL}\n"
        f"💬 Telegram: {TELEGRAM_GROUP}\n\n"
        f"👇 नीचे Menu से ऑप्शन चुनो 👇",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ---------------- Main Menu ----------------
def main_menu():
    menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("🎬 वीडियो देखो", "🔄 शेयर करो")
    menu.row("📊 मेरे पॉइंट्स", "🔗 रेफ़रल लिंक")
    menu.row("🎁 प्रमोशन")
    return menu

# ---------------- Handle All ----------------
@bot.message_handler(func=lambda msg: True)
def handle_all(message):
    user_id = str(message.from_user.id)
    text = message.text
    check_user(user_id)

    if text == "🎬 वीडियो देखो":
        if users[user_id]["videos"] < VIDEO_LIMIT:
            users[user_id]["videos"] += 1
            users[user_id]["points"] += VIDEO_POINTS
            save_data(users)
            bot.reply_to(message, f"✅ आपने वीडियो देखा! {VIDEO_POINTS} कॉइन मिले 🎉")
        else:
            bot.reply_to(message, f"⚠️ {VIDEO_LIMIT} वीडियो आज देख चुके हो। कल फिर ट्राय करो।")

    elif text == "🔄 शेयर करो":
        if users[user_id]["shares"] < SHARE_LIMIT:
            users[user_id]["shares"] += 1
            users[user_id]["points"] += SHARE_POINTS
            save_data(users)
            bot.reply_to(message, f"✅ शेयर सफल! {SHARE_POINTS} कॉइन मिले 🎉")
        else:
            bot.reply_to(message, f"⚠️ {SHARE_LIMIT} शेयर आज कर चुके हो। कल फिर ट्राय करो।")

    elif text == "📊 मेरे पॉइंट्स":
        u = users[user_id]
        bot.reply_to(message,
            f"📊 आपके Stats:\n\n"
            f"⭐ Total Points: {u['points']}\n"
            f"🎬 Videos Watched: {u['videos']}/{VIDEO_LIMIT}\n"
            f"🔄 Shares: {u['shares']}/{SHARE_LIMIT}\n"
            f"👥 Referrals: {u['ref']}"
        )

    elif text == "🔗 रेफ़रल लिंक":
        bot.reply_to(message,
            f"👉 आपका Referral Link:\n"
            f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"
        )

    elif text == "🎁 प्रमोशन":
        if users[user_id]["points"] >= 1000:
            bot.reply_to(message, "✅ Send your YouTube video link. Admin approval के बाद 3 दिन तक प्रमोशन होगा।")
        else:
            bot.reply_to(message, f"⚠️ प्रमोशन के लिए 1000 कॉइन चाहिए। आपके पास {users[user_id]['points']} कॉइन हैं।")

# ---------------- Run Bot ----------------
bot.infinity_polling()