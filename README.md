# YTbot — Telegram Rewards Bot

## Setup
1. `pip install -r requirements.txt`
2. `python db_setup.py`  # bot.db create
3. `cp config.py.example config.py` (या अपनी values भरें)
4. `python main.py`

## Config
- BOT_TOKEN, ADMIN_ID, BOT_USERNAME, WEB_URL, GROUP_URL
- DAILY_CLAIM=70, REFERRAL_BONUS=100, SUBMIT_COST=1280

## Features
- Welcome: Open WebApp, Invite Friends, Join Group
- Keyboard: Wallet, Submit URL, Daily Claim (70/day), Invite
- Referral: new join ⇒ +100 coins to inviter
- Submit URL: costs 1280 coins, logs to admin, persists in bot.db
- Admin Panel button only for ADMIN_ID (totals + last 15 submits)
- 24/7: keep_alive server + infinity_polling

## Deploy (Render)
- New → Web Service → repo चुनें
- Build Command: `pip install -r requirements.txt && python db_setup.py`
- Start Command: `python main.py`
- Free plan पर spin-down हो सकता है; UptimeRobot से हर 5m पिंग दें।