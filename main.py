# main.py
import os
import telebot
from telebot import types
import sqlite3
import time # दैनिक बोनस के लिए टाइमस्टैम्प ट्रैक करने के लिए
from datetime import datetime, timedelta

# ---------- CONFIGURATION ----------
# सुनिश्चित करें कि आपकी config.py फ़ाइल सही ढंग से सेट है
try:
    from config import BOT_TOKEN, WEB_URL, BOT_USERNAME, REFERRAL_POINTS, LINK_SUBMIT_COST, ADMIN_ID
except ImportError:
    print("❌ Error: config.py not found or incomplete. Please create config.py with required variables.")
    exit() # कॉन्फ़िगरेशन के बिना बॉट नहीं चलेगा

# ---------- BOT INIT ----------
bot = telebot.TeleBot(BOT_TOKEN)

# ---------- KEEP ALIVE ----------
# यह अक्सर Replit जैसे प्लेटफॉर्म पर बॉट को चालू रखने के लिए उपयोग किया जाता है।
# यदि आप इसे किसी अन्य स्थायी सर्वर पर चला रहे हैं, तो इसकी आवश्यकता नहीं हो सकती है।
try:
    from keep_alive import keep_alive
    keep_alive()
    print("✅ Keep alive service started.")
except ImportError:
    print("⚠️ Warning: keep_alive.py not found. Bot might stop if not hosted on a persistent server.")
except Exception as e:
    print(f"❌ Error starting keep alive service: {e}")

# ---------- DB SETUP ----------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    coins INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    daily_points INTEGER DEFAULT 0,
    last_daily_bonus TEXT, -- अंतिम दैनिक बोनस का टाइमस्टैम्प
    referred_by INTEGER
)
""")

# Submissions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- SQLite में INTEGER PRIMARY KEY स्वतः ही AUTOINCREMENT होता है
    user_id INTEGER,
    url TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    submission_date TEXT DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
print("✅ Database setup complete.")

# ---------- HELPERS ----------
def get_user(user_id):
    """एक उपयोगकर्ता के डेटा को पुनः प्राप्त करता है।"""
    cursor.execute("SELECT username, coins, referrals, daily_points, last_daily_bonus, referred_by FROM users WHERE id=?", (user_id,))
    return cursor.fetchone()

def add_user(user_id, username):
    """यदि मौजूद न हो तो एक नया उपयोगकर्ता जोड़ता है।"""
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def add_coins(user_id, amount):
    """उपयोगकर्ता के सिक्कों और दैनिक अंकों को अपडेट करता है।"""
    cursor.execute("UPDATE users SET coins = coins + ?, daily_points = daily_points + ? WHERE id=?", 
                   (amount, amount, user_id))
    conn.commit()

def add_referral(ref_id, user_id):
    """एक रेफरल जोड़ता है और रेफरर को सिक्के प्रदान करता है।"""
    cursor.execute("UPDATE users SET referrals = referrals + 1, coins = coins + ? WHERE id=?", (REFERRAL_POINTS, ref_id))
    cursor.execute("UPDATE users SET referred_by = ? WHERE id=?", (ref_id, user_id))
    conn.commit()

def reset_daily_points(user_id):
    """दैनिक अंकों को रीसेट करता है।"""
    cursor.execute("UPDATE users SET daily_points = 0 WHERE id=?", (user_id,))
    conn.commit()

def update_last_daily_bonus_time(user_id):
    """अंतिम दैनिक बोनस टाइमस्टैम्प को अपडेट करता है।"""
    cursor.execute("UPDATE users SET last_daily_bonus = ? WHERE id=?", (datetime.now().isoformat(), user_id))
    conn.commit()

# ---------- COMMAND HANDLERS ----------

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.from_user.username or message.from_user.first_name
    add_user(user_id, username)

    # Referral check
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        user_data = get_user(user_id)
        # सुनिश्चित करें कि रेफरर खुद को रेफर नहीं कर रहा है और उसने पहले से किसी को रेफर नहीं किया है
        if ref_id != user_id and (user_data[5] is None or user_data[5] == 0): # referred_by is None or 0
            add_referral(ref_id, user_id)
            try:
                bot.send_message(ref_id, f"🎉 आपके referral से नए user ने join किया! आपको {REFERRAL_POINTS} Coins मिले ✅")
            except Exception as e:
                print(f"❌ रेफरर को संदेश भेजने में त्रुटि {ref_id}: {e}")
            bot.send_message(user_id, f"✅ आप {ref_id} द्वारा रेफर किए गए हैं और आपको भी कुछ बोनस मिल सकता है (यदि लागू हो)।")

    # Welcome Text
    welcome_text = f"""
🎬 *Video Coin Earner Bot में आपका स्वागत है!* 🎬

नमस्ते {message.from_user.first_name}!  

📹 वीडियो देखो, कॉइन कमाओ और  
💰 अपना YouTube चैनल मोनेटाइजेशन करवाओ ✅  

📌 *कमाई नियम:*  
• प्रत्येक वीडियो = 30 पॉइंट्स  
• दैनिक लिमिट = 100 पॉइंट्स  

👥 *रेफरल सिस्टम:*  
• दोस्तों को इनवाइट करें  
• हर नए यूज़र पर {REFERRAL_POINTS} पॉइंट्स  

⚠️ *महत्वपूर्ण:*  
बॉट यूज़ करने के लिए पहले ग्रुप जॉइन करना ज़रूरी है। (इस सुविधा को लागू करने के लिए आपको ग्रुप सदस्यता जांच जोड़नी होगी)

Welcome 😊
"""

    # Inline buttons
    inline_kb = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton("🎬 Open WebApp", url=WEB_URL)
    invite_btn = types.InlineKeyboardButton("👥 Invite Friends", url=f"https://t.me/{BOT_USERNAME}?start={user_id}")
    inline_kb.add(web_btn, invite_btn)

    bot.send_message(user_id, welcome_text, parse_mode="Markdown", reply_markup=inline_kb)

    # Reply Keyboard
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("🏠 Home", "🎁 Daily Bonus")
    menu.row("🧑‍🤝‍🧑 Invite", "👤 Profile")
    menu.row("💰 Wallet", "📤 Submit URL")
    bot.send_message(user_id, "👇 नीचे दिए गए बटन से आगे बढ़ें:", reply_markup=menu)

# ---------- MESSAGE HANDLER (BUTTONS) ----------
@bot.message_handler(func=lambda msg: True)
def handle_buttons(message):
    user_id = message.chat.id
    user_data = get_user(user_id)
    if not user_data:
        add_user(user_id, message.from_user.username or message.from_user.first_name)
        return bot.send_message(user_id, "❌ आपका डेटा नहीं मिला। कृपया /start दबाएँ।")
    
    username, coins, refs, daily_points, last_daily_bonus_str, referred_by = user_data
    text = message.text

    if text == "🏠 Home":
        # आप यहां एक अधिक विस्तृत होम संदेश जोड़ सकते हैं
        bot.send_message(user_id, f"🎬 Open WebApp: {WEB_URL}")
    
    elif text == "🎁 Daily Bonus":
        now = datetime.now()
        last_bonus_time = None
        if last_daily_bonus_str:
            last_bonus_time = datetime.fromisoformat(last_daily_bonus_str)

        # जांचें कि क्या 24 घंटे बीत चुके हैं
        if last_bonus_time and (now - last_bonus_time) < timedelta(hours=24):
            time_left = timedelta(hours=24) - (now - last_bonus_time)
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.send_message(user_id, f"⏰ आपने पहले ही आज का दैनिक बोनस ले लिया है। {hours} घंटे {minutes} मिनट में फिर से कोशिश करें।")
        else:
            bonus = 30 # दैनिक बोनस के लिए निश्चित राशि

            # यदि दैनिक अंक सीमा पार हो गई है, तो बोनस न दें या उसे कम करें
            if daily_points >= 100: # 100 दैनिक लिमिट
                bot.send_message(user_id, "⚠️ आज की दैनिक अंक सीमा (100) पूरी हो गई है। कल फिर कोशिश करें!")
                # दैनिक बोनस को रीसेट करें ताकि यह अगले दिन से शुरू हो सके
                update_last_daily_bonus_time(user_id)
                # दैनिक अंक रीसेट करें ताकि अगले दिन से नए दैनिक अंक जोड़े जा सकें
                reset_daily_points(user_id) 
            else:
                # सुनिश्चित करें कि बोनस दैनिक अंक सीमा से अधिक न हो
                actual_bonus = min(bonus, 100 - daily_points)
                if actual_bonus > 0:
                    add_coins(user_id, actual_bonus)
                    update_last_daily_bonus_time(user_id)
                    bot.send_message(user_id, f"🎁 आपने {actual_bonus} Coins Daily Bonus में पाए ✅")
                else:
                    bot.send_message(user_id, "⚠️ आज की दैनिक अंक सीमा पूरी हो गई है। कल फिर कोशिश करें!")
                    # यदि सीमा पूरी हो गई है लेकिन 24 घंटे नहीं हुए हैं, तो बस टाइमस्टैम्प अपडेट करें
                    update_last_daily_bonus_time(user_id)
                    reset_daily_points(user_id)


    elif text == "🧑‍🤝‍🧑 Invite":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        bot.send_message(user_id, f"🔗 आपका Referral Link:\n`{ref_link}`\n\nहर invite पर {REFERRAL_POINTS} Coins! इसे अपने दोस्तों के साथ शेयर करें।", parse_mode="Markdown")

    elif text == "👤 Profile":
        profile_text = f"""
👤 *Profile*  

🆔 ID: `{user_id}`  
💳 Balance: *{coins} Coins*  
📊 Daily Points (आज के): *{daily_points}*  
👥 Referrals: *{refs}*  
"""
        bot.send_message(user_id, profile_text, parse_mode="Markdown")

    elif text == "💰 Wallet":
        bot.send_message(user_id, f"💳 आपके Wallet में Coins: {coins}")

    elif text == "📤 Submit URL":
        if coins < LINK_SUBMIT_COST:
            bot.send_message(user_id, f"❌ आपके पास {LINK_SUBMIT_COST} Coins नहीं हैं। आपको और कमाने की ज़रूरत है।")
        else:
            msg = bot.send_message(user_id, "📤 अपना YouTube वीडियो लिंक भेजें (https:// से शुरू होना चाहिए):")
            bot.register_next_step_handler(msg, submit_url_step)
    else:
        # उपयोगकर्ता ने एक अज्ञात बटन दबाया या एक सामान्य पाठ भेजा
        bot.send_message(user_id, "❌ Invalid Option! कृपया नीचे दिए गए बटन का उपयोग करें।")

def submit_url_step(message):
    user_id = message.chat.id
    url = message.text.strip()

    # URL सत्यापन
    if not url.startswith("https://") or not ("youtube.com/watch" in url or "youtu.be/" in url):
        bot.send_message(user_id, "❌ केवल एक वैध YouTube वीडियो URL भेजें (https:// से शुरू होना चाहिए)।")
        return

    user_data = get_user(user_id)
    if not user_data or user_data[1] < LINK_SUBMIT_COST: # सुनिश्चित करें कि उपयोगकर्ता के पास पर्याप्त सिक्के हैं
        bot.send_message(user_id, f"❌ आपके पास इस लिंक को सबमिट करने के लिए पर्याप्त सिक्के नहीं हैं। आवश्यक: {LINK_SUBMIT_COST} Coins।")
        return

    try:
        add_coins(user_id, -LINK_SUBMIT_COST) # सिक्के घटाएँ
        cursor.execute("INSERT INTO submissions (user_id, url) VALUES (?, ?)", (user_id, url))
        conn.commit()

        bot.send_message(user_id, f"✅ आपका लिंक सफलतापूर्वक भेज दिया गया है:\n`{url}`\nआपके अकाउंट से {LINK_SUBMIT_COST} Coins काट लिए गए हैं।", parse_mode="Markdown")
        
        # एडमिन को सूचित करें
        if ADMIN_ID:
            try:
                bot.send_message(ADMIN_ID, f"🔔 *नया URL सबमिशन!* 🔔\n\nUser ID: `{user_id}`\nUsername: @{message.from_user.username or 'N/A'}\nURL: `{url}`\n\nइसे Admin Panel से मैनेज करें: /admin", parse_mode="Markdown")
            except Exception as e:
                print(f"❌ एडमिन को सबमिशन के बारे में सूचित करने में त्रुटि: {e}")
        else:
            print("⚠️ चेतावनी: ADMIN_ID कॉन्फ़िगर नहीं है, एडमिन को URL सबमिशन के बारे में सूचित नहीं किया जा सकता।")

    except Exception as e:
        bot.send_message(user_id, f"❌ लिंक सबमिट करते समय एक त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।")
        print(f"❌ URL सबमिशन में त्रुटि: {e}")

# ---------- ADMIN PANEL ----------
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ एक्सेस अस्वीकृत। आप एडमिन नहीं हैं।")
    
    # कुल उपयोगकर्ता और सिक्के
    cursor.execute("SELECT COUNT(*), SUM(coins) FROM users")
    total_users, total_coins = cursor.fetchone()
    total_users = total_users or 0
    total_coins = total_coins or 0

    # लंबित सबमिशन
    cursor.execute("SELECT id, user_id, url, status, submission_date FROM submissions WHERE status='pending'")
    pending_submissions = cursor.fetchall()

    report = f"""
📊 *एडमिन पैनल रिपोर्ट*  

👥 कुल उपयोगकर्ता: *{total_users}*  
💰 वितरित किए गए कुल सिक्के: *{total_coins}*  

📝 लंबित सबमिशन: *{len(pending_submissions)}*
"""
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

    if pending_submissions:
        bot.send_message(message.chat.id, "*लंबित सबमिशन:*", parse_mode="Markdown")
        for sub in pending_submissions:
            sub_id, u_id, url, status, sub_date = sub
            
            # उपयोगकर्ता का नाम प्राप्त करें
            user_info = get_user(u_id)
            username = user_info[0] if user_info else "Unknown User"

            submission_detail = f"""
ID: `{sub_id}`
User ID: `{u_id}` (@{username})
URL: `{url}`
स्थिति: *{status}*
तिथि: {sub_date}
"""
            # एडमिन के लिए कार्रवाई बटन
            admin_kb = types.InlineKeyboardMarkup()
            approve_btn = types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{sub_id}")
            reject_btn = types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{sub_id}")
            admin_kb.add(approve_btn, reject_btn)
            
            bot.send_message(message.chat.id, submission_detail, parse_mode="Markdown", reply_markup=admin_kb)
    else:
        bot.send_message(message.chat.id, "🎉 कोई लंबित सबमिशन नहीं है।")

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def handle_submission_callback(call):
    admin_id = call.from_user.id
    if admin_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ एक्सेस अस्वीकृत। आप एडमिन नहीं हैं।")
        return

    action, sub_id_str = call.data.split('_')
    sub_id = int(sub_id_str)

    cursor.execute("SELECT user_id, url, status FROM submissions WHERE id=?", (sub_id,))
    submission = cursor.fetchone()

    if not submission:
        bot.answer_callback_query(call.id, "❌ सबमिशन नहीं मिला।")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                              text=f"ID: `{sub_id}` - सबमिशन नहीं मिला या हटा दिया गया।", parse_mode="Markdown")
        return

    user_id, url, current_status = submission

    if current_status != 'pending':
        bot.answer_callback_query(call.id, f"यह सबमिशन पहले ही {current_status} हो चुका है।")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"ID: `{sub_id}`\nUser ID: `{user_id}`\nURL: `{url}`\nस्थिति: *{current_status}* (पहले ही संसाधित)\n", parse_mode="Markdown")
        return

    new_status = 'approved' if action == 'approve' else 'rejected'
    cursor.execute("UPDATE submissions SET status=? WHERE id=?", (new_status, sub_id))
    conn.commit()

    user_info = get_user(user_id)
    username = user_info[0] if user_info else "Unknown User"

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"ID: `{sub_id}`\nUser ID: `{user_id}` (@{username})\nURL: `{url}`\nस्थिति: *{new_status.upper()}*", parse_mode="Markdown")
    bot.answer_callback_query(call.id, f"सबमिशन {new_status} कर दिया गया।")

    # उपयोगकर्ता को सूचित करें
    try:
        if new_status == 'approved':
            bot.send_message(user_id, f"✅ आपका URL सबमिशन (`{url}`) एडमिन द्वारा *स्वीकृत* कर दिया गया है!", parse_mode="Markdown")
        else:
            bot.send_message(user_id, f"❌ आपका URL सबमिशन (`{url}`) एडमिन द्वारा *अस्वीकृत* कर दिया गया है।", parse_mode="Markdown")
    except Exception as e:
        print(f"❌ उपयोगकर्ता {user_id} को सबमिशन अपडेट के बारे में सूचित करने में त्रुटि: {e}")

# ---------- RUN ----------
if __name__ == '__main__':
    print("🤖 Bot is running...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ बॉट चलाते समय गंभीर त्रुटि हुई: {e}")
        # यहां आप त्रुटि लॉगिंग या पुनरारंभ तर्क जोड़ सकते हैं