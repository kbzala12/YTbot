import logging
import sqlite3
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# ================= CONFIG =================
BOT_TOKEN = "7978191312:AAFyWVkBruuR42HTuTd_sQxFaKHBrre0VWw"
ADMIN_ID = 7459795138
WEB_APP_URL = "https://studiokbyt.onrender.com"
GROUP_ID = "@boomupbot10"  # आपका ग्रुप username
BOT_USERNAME = "Bingyt_bot"  # अपने Bot का username डालें

# ================= LOGGING =================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        points INTEGER DEFAULT 0,
        videos INTEGER DEFAULT 0,
        shares INTEGER DEFAULT 0,
        ref INTEGER DEFAULT 0,
        referred_by TEXT
    )''')
    conn.commit()
    conn.close()

def add_user(telegram_id, referred_by=None):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (str(telegram_id),))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (id, points, videos, shares, ref, referred_by) VALUES (?, ?, ?, ?, ?, ?)",
            (str(telegram_id), 0, 0, 0, 0, referred_by)
        )

        # अगर किसी ने refer किया है तो बोनस दो
        if referred_by:
            cursor.execute("SELECT * FROM users WHERE id=?", (str(referred_by),))
            ref_user = cursor.fetchone()
            if ref_user:
                cursor.execute("UPDATE users SET points = points + 100, ref = ref + 1 WHERE id=?", (str(referred_by),))

    conn.commit()
    conn.close()

def get_user(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (str(telegram_id),))
    user = cursor.fetchone()
    conn.close()
    return user

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referral_code = None

    # अगर /start refID दिया गया है तो पकड़ो
    if context.args:
        referral_code = context.args[0]

    add_user(user.id, referral_code)

    welcome_message = f"""
🎬 *Video Coin Earner Bot में आपका स्वागत है!* 🎬

नमस्ते {user.first_name}! 

📹 *वीडियो देखें और कॉइन कमाएं:*
• प्रत्येक वीडियो = 30 पॉइंट्स  
• दैनिक लिमिट = 10 वीडियो  

👥 *रेफरल सिस्टम:*  
• दोस्तों को इनवाइट करें  
• हर नए यूज़र पर 100 पॉइंट्स  

📤 *शेयर सिस्टम:*  
• शेयर करने पर 25 पॉइंट्स  
• लिमिट = 5 शेयर / दिन  

⚠️ *महत्वपूर्ण:* बॉट यूज़ करने के लिए पहले ग्रुप जॉइन करना ज़रूरी है।  

आपका ID: `{user.id}`
"""

    keyboard = [
        [
            InlineKeyboardButton("🚀 ऐप लॉन्च करें", web_app=WebAppInfo(url=WEB_APP_URL)),
            InlineKeyboardButton("👥 ग्रुप जॉइन करें", url=f"https://t.me/{GROUP_ID.replace('@', '')}")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=reply_markup)

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("कृपया पहले /start करें।")
        return

    wallet_message = f"""
💰 *आपका वॉलेट*

🪙 पॉइंट्स: {user[1]}  
📹 वीडियो देखे: {user[2]}/10  
📤 शेयर: {user[3]}/5  
👥 सफल रेफरल्स: {user[4]}  

🔄 स्टेटस: {'✅ लिमिट पूरी' if user[2] >= 10 else '🟡 अभी और कमा सकते हैं'}
"""
    await update.message.reply_text(wallet_message, parse_mode="Markdown")

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("कृपया पहले /start करें।")
        return

    referral_link = f"https://t.me/{BOT_USERNAME}?start={update.effective_user.id}"

    message = f"""
👥 *Invite & Earn System*  

🔗 आपका लिंक:  
{referral_link}  

📊 स्टेट्स:  
• कुल रेफरल्स: {user[4]}  
• कमाई: {user[4] * 100} पॉइंट्स  

💡 अपने दोस्तों को यह लिंक भेजें।  
"""
    keyboard = [[InlineKeyboardButton("📤 शेयर करें", switch_inline_query=referral_link)]]
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """
🎬 *Bot Commands*

/start - शुरू करें  
/wallet - वॉलेट देखें  
/referral - रेफरल लिंक  
/help - मदद  

👉 वीडियो देखें, रेफरल करें और पॉइंट्स कमाएं।
"""
    await update.message.reply_text(msg, parse_mode="Markdown")

# ================= MAIN =================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wallet", wallet))
    app.add_handler(CommandHandler("referral", referral))
    app.add_handler(CommandHandler("help", help_command))

    print("🤖 Bot with Invite System is running...")
    app.run_polling()

if __name__ == "__main__":
    main()