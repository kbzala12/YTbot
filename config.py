import os

# ---------------- Bot Credentials ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN","7978191312:AAFFaOkxBSI9YoN4uR3I5FtZbfQNojT8F4U")  # Telegram Bot Token
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7459795138))  # Admin Telegram ID
BOT_USERNAME = os.environ.get("BOT_USERNAME", "Bingyt_bot")  # Bot Username

# ---------------- WebApp / Links ----------------
WEB_URL = os.environ.get("WEB_URL", "https://studiokbyt.onrender.com/") 

# ---------------- Bot Config ----------------
LINK_SUBMIT_COST = int(os.environ.get("LINK_SUBMIT_COST", 1280))  # Cost to submit URL
REFERRAL_POINTS = int(os.environ.get("REFERRAL_POINTS", 100))    # Coins per new referral