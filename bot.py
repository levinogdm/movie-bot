import sqlite3, telebot, threading, time
from flask import Flask

# Configuration
BOT_TOKEN = "8838381613:AAHCg0HlEnZp3yeNELd1GpSfvYHyL4Q8paA"
PRIVATE_CHANNEL_ID = -1004307986554
MAIN_CHANNEL_ID = -1004469439263
bot = telebot.TeleBot(BOT_TOKEN)

# 1. Web Server for 24/7 uptime
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Active!"

# 2. Database setup
def init_db():
    conn = sqlite3.connect("movies.db")
    conn.execute('CREATE TABLE IF NOT EXISTS movies (name TEXT, msg_id INTEGER, photo_id TEXT)')
    conn.commit()
    conn.close()

# 3. Auto-delete function (2 minutes)
def auto_del(chat_id, msg_id):
    time.sleep(120)
    try: bot.delete_message(chat_id, msg_id)
    except: pass

# 4. Handler for files uploaded to Private Channel
@bot.channel_post_handler(content_types=['document', 'video', 'photo'])
def handle_upload(m):
    if m.chat.id == PRIVATE_CHANNEL_ID:
        name = (m.caption or "Movie").lower()
        photo_id = m.photo[-1].file_id if m.photo else None
        
        conn = sqlite3.connect("movies.db")
        conn.execute("INSERT INTO movies VALUES (?, ?, ?)", (name, m.message_id, photo_id))
        conn.commit(); conn.close()
        
        # Notification to Main Channel
        msg = f"🆕 New Movie Available: {name.upper()}\n\nClick the link below to download: @medart_hub_bot"
        bot.send_message(MAIN_CHANNEL_ID, msg)

# 5. Bot Search & Subscription Check
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Welcome! Please type the movie name to get the download link.")

@bot.message_handler(func=lambda m: True)
def search(m):
    # Check if user joined the main channel
    try:
        status = bot.get_chat_member(MAIN_CHANNEL_ID, m.from_user.id).status
        if status == 'left':
            bot.reply_to(m, "Please join our main channel first to download movies!")
            return
    except: pass
    
    conn = sqlite3.connect("movies.db")
    res = conn.execute("SELECT msg_id FROM movies WHERE name LIKE ?", (f"%{m.text.lower()}%",)).fetchall()
    conn.close()
    
    if not res:
        bot.reply_to(m, "Sorry, this movie is not available.")
        return

    for (msg_id,) in res:
        # Copy file from private channel
        sent = bot.copy_message(m.chat.id, PRIVATE_CHANNEL_ID, msg_id)
        # Start auto-delete timer
        threading.Thread(target=auto_del, args=(m.chat.id, sent.message_id)).start()

# Server & Bot startup
if __name__ == '__main__':
    init_db()
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()