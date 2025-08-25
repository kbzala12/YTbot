from flask import Flask
bot = Flask('')
@bot.route('/')
def home():
    return "Alive"

if __name__ == '__main__':
    bot.run()