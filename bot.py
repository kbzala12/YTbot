import telebot
from telebot import types
from config import BOT_TOKEN, ADMIN_ID, WEB_URL

bot = telebot.TeleBot(BOT_TOKEN)

# 🗂 User Data (memory)
users = {}

# 🛠 Check & Create User
def check_user(user_id):
    if user_id not in users:
        users[user_id] = {"points": 0, "invites": 0}

# 🎬 /start Command
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)

    # अगर यूज़र Invite से आया है
    args = message.text.split()
    if len(args) > 1:  
        referrer = args[1]
        if referrer != user_id:   # खुद को invite करने से रोकना
            check_user(referrer)
            users[referrer]["points"] += 100
            users[referrer]["invites"] += 1
            bot.send_message(referrer, "🎉 आपके Invite से नया यूज़र जुड़ा! +100 Coins आपके Wallet में जोड़ दिए गए।")

    check_user(user_id)

    # मेन्यू
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 प्रोफाइल", "💰 Wallet")
    menu.row("🌐 Web Open", "👥 Invite")

    welcome_text = (
        "👋 स्वागत है आपके Simple Bot में!\n\n"
        "🎯 यहाँ आप कर सकते हैं:\n"
        "🎁 Coins कमाओ\n"
        "🌐 WebApp खोलो\n"
        "👥 Invite करके 100 Coins पाओ\n"
        "💰 Wallet चेक करो\n\n"
        "👇 नीचे से Menu चुनें"
    )
    bot.send_message(user_id, welcome_text, reply_markup=menu)

# 🔘 Menu Handler
@bot.message_handler(func=lambda msg: True)
def handle_all(message):
    user_id = str(message.from_user.id)
    check_user(user_id)
    text = message.text

    if text == "📊 प्रोफाइल":
        bot.reply_to(message, f"👤 User ID: {user_id}\n🎯 Invites: {users[user_id]['invites']}")
    
    elif text == "💰 Wallet":
        bot.reply_to(message, f"💰 आपके Wallet Balance: {users[user_id]['points']} Coins")
    
    elif text == "🌐 Web Open":
        markup = types.InlineKeyboardMarkup()
        web_btn = types.InlineKeyboardButton("🚀 Open WebApp", web_app=types.WebAppInfo(WEB_URL))
        markup.add(web_btn)
        bot.send_message(user_id, "👇 नीचे क्लिक करके अपना WebApp खोलें:", reply_markup=markup)
    
    elif text == "👥 Invite":
        invite_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        bot.reply_to(message, f"👥 अपना Invite Link शेयर करें:\n\n{invite_link}\n\n✅ हर नए यूज़र पर आपको +100 Coins मिलेंगे।")
    
    elif text == "👑 Admin":
        if int(user_id) == ADMIN_ID:
            bot.reply_to(message, "✅ आप Admin हैं!")
        else:
            bot.reply_to(message, "⛔ यह फीचर सिर्फ़ Admin के लिए है।")

# ♾ Bot Run
bot.infinity_polling()
