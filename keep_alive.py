from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.get("/")
def home():
    return "OK - Telegram bot alive"

def run():
    # 0.0.0.0 पर bind ताकि Render/Replit इसे पिंग कर सकें
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()