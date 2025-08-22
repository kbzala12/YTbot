import telebot
from telebot import types
from config import BOT_TOKEN, ADMIN_ID, WEB_URL

bot = telebot.TeleBot(BOT_TOKEN)

# 🗂 User Data (मेमोरी में)
users = {}

# 🔗 Referral Data
referrals = {}

# 🛠 Check & Create User
def check_user(user_id, ref_id=None):
    if user_id not in users:
        # नए user को 100 पॉइंट्स अगर referral से आया है
        initial_points = 100 if ref_id and ref_id in users else 0
        users[user_id] = {"points": initial_points}
        
        # Referral देने वाले को 100 पॉइंट्स देना
        if ref_id and ref_id in users:
            users[ref_id]["points"] += 100
            bot.send_message(ref_id, f"🎉 आपके referral से नए user ने join किया! आपको 100 पॉइंट्स मिले।")
        
        # Referral track
        if ref_id:
            referrals[user_id] = ref_id

# 🎬 /start Command
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 else None  # /start <ref_id>
    
    check_user(user_id, ref_id)

    # मेन्यू
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 प्रोफाइल", "🎁 पॉइंट्स पाओ")
    menu.row("🌐 Web Open", "💰 Wallet")
    menu.row("🔗 Invite")
    bot.send_message(user_id, "👋 स्वागत है Simple Bot में!", reply_markup=menu)

# 🔘 Menu Handler
@bot.message_handler(func=lambda msg: True)
def handle_all(message):
    user_id = message.from_user.id
    check_user(user_id)
    text = message.text

    if text == "📊 प्रोफाइल":
        bot.reply_to(message, f"👤 आपके पॉइंट्स: {users[user_id]['points']}")
    elif text == "🎁 पॉइंट्स पाओ":
        users[user_id]["points"] += 10
        bot.reply_to(message, "✅ आपको 10 पॉइंट्स मिले!")
    elif text == "🌐 Web Open":
        markup = types.InlineKeyboardMarkup()
        web_btn = types.InlineKeyboardButton("🚀 Open WebApp", web_app=types.WebAppInfo(WEB_URL))
        markup.add(web_btn)
        bot.send_message(user_id, "👇 नीचे क्लिक करके अपना WebApp खोलें:", reply_markup=markup)
    elif text == "💰 Wallet":
        bot.reply_to(message, f"💵 आपके Wallet में पॉइंट्स: {users[user_id]['points']}")
    elif text == "🔗 Invite":
        invite_link = f"https://t.me/YourBotUsername?start={user_id}"
        bot.reply_to(message, f"🎯 अपने दोस्तों को invite करें और 100 पॉइंट्स पाएं!\n\nInvite Link:\n{invite_link}")
    elif text == "👑 Admin":
        if user_id == ADMIN_ID:
            bot.reply_to(message, "✅ आप Admin हैं!")
        else:
            bot.reply_to(message, "⛔ यह फीचर सिर्फ़ Admin के लिए है।")

# ♾ Bot Run
bot.infinity_polling()