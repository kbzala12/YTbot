# 🎬 /start Command
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    check_user(user_id, ref_id)

    welcome_text = f"""
🎬 Video Coin Earner Bot में आपका स्वागत है! 🎬

नमस्ते {message.from_user.first_name}!

📹 वीडियो देखो, कॉइन कमाओ और  
💰 अपना YouTube चैनल मोनेटाइजेशन करवाओ ✅  

📌 कमाई नियम:
• प्रत्येक वीडियो = {VIDEO_POINTS} पॉइंट्स  
• दैनिक लिमिट = {DAILY_POINT_LIMIT} पॉइंट्स  

👥 रेफरल सिस्टम:  
• दोस्तों को इनवाइट करें  
• हर नए यूज़र पर {REFERRAL_POINTS} पॉइंट्स  

⚠️ महत्वपूर्ण: बॉट यूज़ करने के लिए पहले ग्रुप जॉइन करना ज़रूरी है।  

आपका ID: {user_id}
"""

    # Inline keyboard for WebApp
    markup = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🚀 Open WebApp", web_app=types.WebAppInfo(WEB_URL))
    markup.add(web_btn)

    bot.send_message(user_id, welcome_text, reply_markup=markup)

    # ✅ Reply keyboard with Invite button
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📊 प्रोफाइल", "🎁 पॉइंट्स पाओ")
    menu.row("💰 Wallet", "🔗 Invite Friends")  # ✅ Invite button added
    bot.send_message(user_id, "👇 नीचे दिए गए बटन से आगे बढ़ें:", reply_markup=menu)