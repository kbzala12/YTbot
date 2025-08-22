import telebot
from telebot import types
from config import BOT_TOKEN, ADMIN_ID, WEB_URL

bot = telebot.TeleBot(BOT_TOKEN)

# 🗂 User Data (Memory)
users = {}
video_count = {}  # daily video count
referrals = {}    # referral tracking

DAILY_VIDEO_LIMIT = 50
VIDEO_POINTS = 30
REFERRAL_POINTS = 100

# 🛠 Check & Create User
def check_user(user_id, ref_id=None):
    if user_id not in users:
        # Referral से आए नए user को 100 पॉइंट्स
        initial_points = REFERRAL_POINTS if ref_id and ref_id in users else 0
        users[user_id] = {"points": initial_points}
        video_count[user_id] = 0

        # Referral देने वाले को भी 100 पॉइंट्स
        if ref_id and ref_id in users:
            users[ref_id]["points"] += REFERRAL_POINTS
            bot.send_message(ref_id, f"🎉 आपके referral से नए user ने join किया! आपको {REFERRAL_POINTS} पॉइंट्स मिले।")

        # Referral track
        if ref_id:
            referrals[user_id] = ref_id

# 🎬 /start Command
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None  # /start <ref_id>
    
    check_user(user_id, ref_id)

    # 👋 Welcome Message
    welcome_text = f"""
🎬 Video Coin Earner Bot में आपका स्वागत है! 🎬

नमस्ते {message.from_user.first_name}!

📹 वीडियो देखें और कॉइन कमाएं:
• प्रत्येक वीडियो = {VIDEO_POINTS} पॉइंट्स  
• दैनिक लिमिट = {DAILY_VIDEO_LIMIT} वीडियो  

👥 रेफरल सिस्टम:  
• दोस्तों को इनवाइट करें  
• हर नए यूज़र पर {REFERRAL_POINTS} पॉइंट्स  

⚠️ महत्वपूर्ण: बॉट यूज़ करने के लिए पहले ग्रुप जॉइन करना ज़रूरी है।  

आपका ID: {user_id}
"""

    # Inline Buttons: Web Open + Invite
    markup = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🚀 Open WebApp", web_app=types.WebAppInfo(WEB_URL))
    invite_link = f"https://t.me/YourBotUsername?start={user_id}"
    invite_btn = types.InlineKeyboardButton("🔗 Invite Friends", url=invite_link)
    markup.add(web_btn, invite_btn)

    # Send welcome message with buttons
    bot.send_message(user_id, welcome_text, reply_markup=markup)

    # ReplyKeyboard for Wallet & Profile
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 प्रोफाइल", "🎁 पॉइंट्स पाओ")
    menu.row("💰 Wallet")
    bot.send_message(user_id, "नीचे दिए गए बटन से आगे बढ़ें:", reply_markup=menu)

# 🔘 Menu Handler
@bot.message_handler(func=lambda msg: True)
def handle_all(message):
    user_id = message.from_user.id
    check_user(user_id)
    text = message.text

    if text == "📊 प्रोफाइल":
        bot.reply_to(message, f"👤 आपके पॉइंट्स: {users[user_id]['points']}")
    elif text == "🎁 पॉइंट्स पाओ":
        # Video points with daily limit
        if video_count[user_id] < DAILY_VIDEO_LIMIT:
            users[user_id]["points"] += VIDEO_POINTS
            video_count[user_id] += 1
            bot.reply_to(message, f"✅ आपको {VIDEO_POINTS} पॉइंट्स मिले! ({video_count[user_id]}/{DAILY_VIDEO_LIMIT} आज)")
        else:
            bot.reply_to(message, f"⚠️ आज की वीडियो लिमिट पूरी हो गई है। कल फिर कोशिश करें!")
    elif text == "💰 Wallet":
        bot.reply_to(message, f"💵 आपके Wallet में पॉइंट्स: {users[user_id]['points']}")
    elif text == "👑 Admin":
        if user_id == ADMIN_ID:
            bot.reply_to(message, "✅ आप Admin हैं!")
        else:
            bot.reply_to(message, "⛔ यह फीचर सिर्फ़ Admin के लिए है।")

# ♾ Bot Run
bot.infinity_polling()