K B zala:
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = 7978191312:AAFyWVkBruuR42HTuTd_sQxFaKHBrre0VWw
ADMIN_ID =7459795138
WEB_APP_URL = "https://0e8b2f63-6f1c-4921-9feb-42115ce5360f-00-2amqt62lj9glu.picard.replit.dev"
GROUP_ID = @boomupbot10"  # Update with your group username

def generate_referral_code():
    import random
    import string
    return f"REF{random.randint(1000, 9999)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}"

def get_or_create_user(telegram_id, username=None, first_name=None, last_name=None, referral_code=None):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(telegram_id),))
    user = cursor.fetchone()
    
    if not user:
        # Create new user
        ref_code = generate_referral_code()
        cursor.execute('''
            INSERT INTO users (telegram_id, username, first_name, last_name, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(telegram_id), username, first_name, last_name, ref_code, referral_code))
        
        user_id = cursor.lastrowid
        
        # Handle referral bonus
        if referral_code:
            cursor.execute('SELECT id FROM users WHERE referral_code = ?', (referral_code,))
            referrer = cursor.fetchone()
            
            if referrer:
                referrer_id = referrer[0]
                
                # Add bonus to referrer
                cursor.execute('''
                    UPDATE users 
                    SET coin_balance = coin_balance + 100, total_coins_earned = total_coins_earned + 100
                    WHERE id = ?
                ''', (referrer_id,))
                
                # Create referral record
                cursor.execute('''
                    INSERT INTO referrals (referrer_id, referred_user_id)
                    VALUES (?, ?)
                ''', (referrer_id, user_id))
        
        conn.commit()
        
        # Get the created user
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
    
    conn.close()
    return user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler"""
    user = update.effective_user
    
    # Extract referral code from command
    referral_code = None
    if context.args:
        referral_code = context.args[0]
    
    # Get or create user
    db_user = get_or_create_user(
        user.id, 
        user.username, 
        user.first_name, 
        user.last_name, 
        referral_code
    )
    
    welcome_message = f"""
🎬 *Video Coin Earner Bot में आपका स्वागत है!* 🎬

नमस्ते {user.first_name}! 

📹 *वीडियो देखें और कॉइन कमाएं:*
• प्रत्येक वीडियो के लिए 30 कॉइन्स
• दैनिक लिमिट: 900 कॉइन्स
• 100+ भारतीय YouTube वीडियो

👥 *रेफरल सिस्टम:*
• दोस्तों को इनवाइट करें
• प्रत्येक नए यूजर के लिए 100 कॉइन्स

🔗 *URL जमा करें:*
• अपना YouTube वीडियो जमा करें
• 200 कॉइन्स पाएं

⚠️ *महत्वपूर्ण:* बॉट का उपयोग करने के लिए पहले हमारे ग्रुप में जॉइन करना आवश्यक है।

आपका रेफरल कोड: {db_user[9] if db_user else 'ERROR'}
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🚀 ऐप लॉन्च करें", web_app=WebAppInfo(url=WEB_APP_URL)),
            InlineKeyboardButton("👥 ग्रुप जॉइन करें", url=f"https://t.me/{GROUP_ID.replace('@', '')}")
        ],
        [
            InlineKeyboardButton(

"📢 दोस्तों को इनवाइट करें", 
                switch_inline_query=f"🎬 Video Coin Earner Bot से कॉइन्स कमाएं! {WEB_APP_URL}?ref={db_user[9] if db_user else ''}"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message, 
        parse_mode='Markdown', 
        reply_markup=reply_markup
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify group membership"""
    user = update.effective_user
    
    try:
        # Check if user is in the group
        chat_member = await context.bot.get_chat_member(GROUP_ID, user.id)
        is_member = chat_member.status in ['member', 'administrator', 'creator']
        
        if is_member:
            # Update user group membership status
            conn = sqlite3.connect('db.sqlite')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_group_member = 1 WHERE telegram_id = ?', (str(user.id),))
            conn.commit()
            conn.close()
            
            keyboard = [[InlineKeyboardButton("🚀 ऐप लॉन्च करें", web_app=WebAppInfo(url=WEB_APP_URL))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                '✅ बधाई हो! आप सफलतापूर्वक वेरिफाई हो गए हैं। अब आप कॉइन्स कमाना शुरू कर सकते हैं।',
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("👥 ग्रुप जॉइन करें", url=f"https://t.me/{GROUP_ID.replace('@', '')}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                '❌ आप अभी भी ग्रुप के सदस्य नहीं हैं। कृपया पहले ग्रुप जॉइन करें।',
                reply_markup=reply_markup
            )
    except Exception as e:
        await update.message.reply_text('वेरिफिकेशन में समस्या हुई। कृपया बाद में कोशिश करें।')

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Wallet command handler"""
    user = update.effective_user
    
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(user.id),))
    db_user = cursor.fetchone()
    
    if not db_user:
        await update.message.reply_text('कृपया पहले /start कमांड का उपयोग करें।')
        return
    
    # Get referral count
    cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (db_user[0],))
    referral_count = cursor.fetchone()[0]
    
    conn.close()
    
    wallet_message = f"""
💰 *आपका वॉलेट*

🪙 *उपलब्ध कॉइन्स:* {db_user[5]}
📊 *कुल कमाए गए:* {db_user[7]}
📹 *देखे गए वीडियो:* {db_user[8]}
👥 *सफल रेफरल्स:* {referral_count}
📅 *आज कमाए गए:* {db_user[6]}/900

🔄 *आज का स्टेटस:* {'✅ दैनिक लिमिट पूरी' if db_user[6] >= 900 else '🟡 कमाना जारी रखें'}
"""
    
    keyboard = [[InlineKeyboardButton("🚀 ऐप लॉन्च करें", web_app=WebAppInfo(url=WEB_APP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        wallet_message, 
        parse_mode='Markdown', 
        reply_markup=reply_markup
    )

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Referral command handler"""
    user = update.effective_user
    
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(user.id),))
    db_user = cursor.fetchone()
    
    if not db_user:
        await update.message.reply_text('कृपया पहले /start कमांड का उपयोग करें।')
        return
    
    # Get referral count
    cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (db_user[0],))
    referral_count = cursor.fetchone()[0]
    
    conn.close()
    
    referral_link = f"{WEB_APP_URL}?ref={db_user[9]}"
    
    referral_message = f"""
👥 *रेफरल सिस्टम*

🔗 *आपका रेफरल लिंक:*
{referral_link}

📊 *आपके स्टेट्स:*
• कुल रेफरल्स: {referral_count}
• रेफरल से कमाया: {referral_count * 100} कॉइन्स

💡 *कैसे काम करता है:*
• दोस्तों को अपना लिंक भेजें
• जब वे जॉइन करते हैं, आपको 100 कॉइन्स मिलते हैं
• कोई लिमिट नहीं!
"""
    
    keyboard = [
        [InlineKeyboardButton(
            "📤 शेयर करें", 
            switch_inline_query=f"🎬 Video Coin Earner Bot से कॉइन्स कमाएं! {referral_link}"
        )],
        [InlineKeyboardButton("🚀 ऐप लॉन्च करें", web_app=WebAppInfo(url=WEB_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        referral_message, 
        parse_mode='Markdown', 
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command handler"""
    help_message = """
🎬 *Video Coin Earner Bot Commands*

/start - बॉट शुरू करें
/wallet - वॉलेट देखें  
/referral - रेफरल जानकारी
/verify - ग्रुप मेंबरशिप वेरिफाई करें
/help - यह मैसेज

📱 *मुख्य फीचर्स:*
• वीडियो देखकर कॉइन्स कमाएं
• दोस्तों को रेफर करें
• YouTube URLs जमा करें
• दैनिक 900 कॉइन्स की लिमिट

🔔 *सपोर्ट:* @admin_username
"""
    
    await update.message.reply_text(help_message, parse_mode='Markdown')

def main() -> None:
    """Start the bot."""
    # Initialize database
    from app import init_db
    init_db()
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("verify", verify))
    application.add_handler(CommandHandler("wallet", wallet))
    application.add_handler(CommandHandler("referral", referral))
    application.add_handler(CommandHandler("help", help_command))
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if name == 'main':
    main()