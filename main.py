import os
import sqlite3
import datetime
import telebot
from telebot import types

from config import *
from keep_alive import keep_alive

# ---- Keep Alive (for Render/Replit + UptimeRobot) ----
keep_alive()

# ---- Telegram Bot ----
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ---- DB Connection (persistent) ----
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# Helpers
def ensure_user(user_id: int, username: str):
    cur.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (user_id, username))
    conn.commit()

def get_user(user_id: int):
    cur.execute("SELECT username, coins, invites, last_claim FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()

def add_coins(user_id: int, amount: int):
    cur.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

def set_last_claim_today(user_id: int):
    today = datetime.date.today().isoformat()
    cur.execute("UPDATE users SET last_claim=? WHERE user_id=?", (today, user_id))
    conn.commit()

def can_claim_today(last_claim: str | None) -> bool:
    return (last_claim or "") != datetime.date.today().isoformat()

def add_referral(inviter_id: int):
    cur.execute("UPDATE users SET invites = invites + 1, coins = coins + ? WHERE user_id=?", (REFERRAL_BONUS, inviter_id))
    conn.commit()

def save_url(user_id: int, url: str):
    cur.execute("INSERT INTO submits (user_id, url) VALUES (?,?)", (user_id, url))
    conn.commit()

def admin_keyboard_row(kb: types.ReplyKeyboardMarkup, user_id: int):
    if user_id == ADMIN_ID:
        kb.row("👨‍💻 Admin Panel")

# ---- /start ----
@bot.message_handler(commands=["start"])
def cmd_start(message):
    user_id = message.chat.id
    username = message.from_user.username or message.from_user.first_name
    ensure_user(user_id, username)

    # Referral
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id != user_id:
            add_referral(ref_id)
            try:
                bot.send_message(ref_id, f"🎉 आपके referral से नया user जुड़ा! आपको *{REFERRAL_BONUS}* coins मिले ✅")
            except:
                pass

    welcome = (
        "🎬 *Video Coin Earner Bot*\n\n"
        f"नमस्ते {message.from_user.first_name}!\n\n"
        "📹 वीडियो देखो, कॉइन कमाओ\n"
        "💰 और अपना YouTube चैनल प्रमोट करो ✅"
    )

    # Inline (Welcome) buttons: Open, Invite, Join
    ikb = types.InlineKeyboardMarkup()
    b_web   = types.InlineKeyboardButton("🎬 Open WebApp", url=WEB_URL)
    b_inv   = types.InlineKeyboardButton("👥 Invite Friends", url=f"https://t.me/{BOT_USERNAME}?start={user_id}")
    b_join  = types.InlineKeyboardButton("📌 Join Group", url=GROUP_URL)
    ikb.add(b_web, b_inv, b_join)

    bot.send_message(user_id, welcome, reply_markup=ikb)

    # Reply Keyboard: Wallet, Submit URL, Daily Claim, Invite (+ Admin for owner)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💰 Wallet", "📤 Submit URL")
    kb.row("🎁 Daily Claim", "🧑‍🤝‍🧑 Invite")
    admin_keyboard_row(kb, user_id)
    bot.send_message(user_id, "👇 नीचे दिए गए बटन इस्तेमाल करें:", reply_markup=kb)

# ---- Buttons handler ----
@bot.message_handler(func=lambda m: True)
def on_message(message):
    user_id = message.chat.id
    rec = get_user(user_id)
    if not rec:
        return bot.send_message(user_id, "❌ पहले /start दबाएँ।")
    username, coins, invites, last_claim = rec

    text = message.text

    if text == "💰 Wallet":
        return bot.send_message(user_id, f"💳 आपके Wallet में: *{coins}* coins")

    if text == "🎁 Daily Claim":
        if can_claim_today(last_claim):
            add_coins(user_id, DAILY_CLAIM)
            set_last_claim_today(user_id)
            return bot.send_message(user_id, f"🎁 आज के *{DAILY_CLAIM}* coins claim हो गए ✅")
        else:
            return bot.send_message(user_id, "⚠️ आपने आज का claim ले लिया है। कल फिर आएं!")

    if text == "🧑‍🤝‍🧑 Invite":
        ref = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        return bot.send_message(user_id, f"🔗 आपका referral link:\n{ref}\nहर नए यूज़र पर *{REFERRAL_BONUS}* coins!")

    if text == "📤 Submit URL":
        if coins < SUBMIT_COST:
            return bot.send_message(user_id, f"❌ आपके पास *{SUBMIT_COST}* coins नहीं हैं।")
        msg = bot.send_message(user_id, f"📤 अपना लिंक भेजें (क़ीमत: {SUBMIT_COST} coins):")
        return bot.register_next_step_handler(msg, handle_submit)

    if text == "👨‍💻 Admin Panel" and user_id == ADMIN_ID:
        cur.execute("SELECT COUNT(*), SUM(coins) FROM users")
        total_users, total_coins = cur.fetchone()
        cur.execute("SELECT id, user_id, url, status, submit_date FROM submits ORDER BY id DESC LIMIT 15")
        rows = cur.fetchall()
        if rows:
            lines = [f"#{r[0]} | UID:{r[1]} | {r[2]} | {r[3]} | {r[4]}" for r in rows]
            urls_block = "\n".join(lines)
        else:
            urls_block = "—"
        report = (
            "📊 *Admin Panel*\n\n"
            f"👥 Total Users: *{(total_users or 0)}*\n"
            f"💰 Total Coins (in DB): *{(total_coins or 0)}*\n\n"
            f"📤 Recent Submits (max 15):\n{urls_block}"
        )
        return bot.send_message(user_id, report)

    # Fallback
    bot.send_message(user_id, "❌ Invalid option. नीचे दिए गए buttons इस्तेमाल करें।")

def handle_submit(message):
    user_id = message.chat.id
    url = (message.text or "").strip()
    # deduct and save
    add_coins(user_id, -SUBMIT_COST)
    save_url(user_id, url)
    bot.send_message(user_id, f"✅ आपका लिंक submit हुआ:\n{url}")
    # notify admin
    try:
        bot.send_message(ADMIN_ID, f"🔔 नया URL submit:\n{url}\nUser ID: {user_id}")
    except:
        pass

# ---- Run 24/7 ----
print("🤖 Bot is running 24/7...")
bot.infinity_polling(timeout=60, long_polling_timeout=60, allowed_updates=telebot.util.update_types)