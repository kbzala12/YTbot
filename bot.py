import telebot
from telebot import types
from config import BOT_TOKEN, ADMIN_ID, WEB_URL

bot = telebot.TeleBot(BOT_TOKEN)

# 🗂 User Data (मेमोरी में)
users = {}

# 🛠 Check & Create User
def check_user(user_id):
    if user_id not in users:
        users[user_id] = {"points": 0}

# 🎬 /start Command
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    check_user(user_id)

    # मेन्यू
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 प्रोफाइल", "🎁 पॉइंट्स पाओ")
    menu.row("🌐 Web Open")
    bot.send_message(user_id, "👋 स्वागत है Simple Bot में!", reply_markup=menu)

# 🔘 Menu Handler
@bot.message_handler(func=lambda msg: True)
def handle_all(message):
    user_id = message.from_user.id
    check_user(user_id)
    text = message.text

    if text == "📊 प्रोफाइल":
        bot.reply_to(message, f"👤 Points: {users[user_id]['points']}")
    elif text == "🎁 पॉइंट्स पाओ":
        users[user_id]["points"] += 10
        bot.reply_to(message, "✅ आपको 10 पॉइंट्स मिले!")
    elif text == "🌐 Web Open":
        markup = types.InlineKeyboardMarkup()
        web_btn = types.InlineKeyboardButton("🚀 Open WebApp", web_app=types.WebAppInfo(WEB_URL))
        markup.add(web_btn)
        bot.send_message(user_id, "👇 नीचे क्लिक करके अपना WebApp खोलें:", reply_markup=markup)
    elif text == "👑 Admin":
        if user_id == ADMIN_ID:
            bot.reply_to(message, "✅ आप Admin हैं!")
        else:
            bot.reply_to(message, "⛔ यह फीचर सिर्फ़ Admin के लिए है।")

# ♾ Bot Run
bot.infinity_polling()
