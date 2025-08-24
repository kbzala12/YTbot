import os

# ---------------- Bot Credentials ----------------
BOT_TOKEN = os.environ.get("7978191312:AAFyWVkBruuR42HTuTd_sQxFaKHBrre0VWw")  # Telegram Bot Token
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7459795138))  # Admin Telegram ID
BOT_USERNAME = os.environ.get("BOT_USERNAME", "Bingyt_bot")  # Bot Username

# ---------------- WebApp / Links ----------------
WEB_URL = os.environ.get("WEB_URL", "https://studiokbyt.onrender.com/")  # Your WebApp URL
VIP_YT_CHANNEL = os.environ.get("VIP_YT_CHANNEL", "https://youtube.com/@kishorsinhzala")  # VIP YouTube Channel

# ---------------- Bot Config ----------------
LINK_SUBMIT_COST = int(os.environ.get("LINK_SUBMIT_COST", 1280))  # Cost to submit URL
REFERRAL_POINTS = int(os.environ.get("REFERRAL_POINTS", 100))    # Coins per new referral