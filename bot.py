import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =========================
# 🔑 Config
# =========================
BOT_TOKEN = "7978191312:AAFyWVkBruuR42HTuTd_sQxFaKHBrre0VWw"
ADMIN_ID = 7459795138
WEB_URL = "https://studiokbyt.onrender.com/"
BOT_USERNAME = "Kingyt1k_bot"

# =========================
# 📂 Database Init
# =========================
def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 user_id INTEGER PRIMARY KEY,
                 coins INTEGER DEFAULT 0,
                 referrer_id INTEGER)""")
    conn.commit()
    conn.close()

init_db()

# =========================
# 🟢 Start Command
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # referral check
    ref_id = None
    if context.args:
        try:
            ref_id = int(context.args[0])
        except:
            pass

    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_data = c.fetchone()

    if not user_data:
        # नया यूज़र add
        c.execute("INSERT INTO users (user_id, coins, referrer_id) VALUES (?, ?, ?)", (user_id, 0, ref_id))
        conn.commit()

        if ref_id:
            # रेफ़र करने वाले को 100 coins
            c.execute("UPDATE users SET coins = coins + 100 WHERE user_id=?", (ref_id,))
            conn.commit()

    conn.close()

    # Buttons
    buttons = [
        [InlineKeyboardButton("🚀 Web Open", web_app=WebAppInfo(WEB_URL))],
        [InlineKeyboardButton("👥 Invite", url=f"https://t.me/{BOT_USERNAME}?start={user_id}")],
        [InlineKeyboardButton("💰 Wallet", callback_data="wallet")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        f"🎬 *Video Coin Earner Bot* में आपका स्वागत है {user.first_name}!\n\n"
        "📹 वीडियो देखो और कॉइन कमाओ\n"
        "👥 दोस्तों को Invite करके Extra कमाओ\n"
        "💰 Wallet में अपना Balance देखो\n\n"
        "👉 YouTube चैनल Monetization का असली रास्ता 🚀",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# =========================
# 💰 Wallet Handler
# =========================
async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()

    balance = result[0] if result else 0
    await query.answer()
    await query.edit_message_text(f"👤 आपका Wallet Balance: *{balance} coins*", parse_mode="Markdown")

# =========================
# Run Bot
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(wallet, pattern="wallet"))

    app.run_polling()

if __name__ == "__main__":
    main()