import sqlite3
import telebot
import time
import threading
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# നിങ്ങളുടെ വിവരങ്ങൾ
BOT_TOKEN = "8838381613:AAHCg0HlEnZp3yeNELd1GpSfvYHyL4Q8paA"
PRIVATE_CHANNEL_ID = -1004307986554
MAIN_CHANNEL_ID = -1004469439263
BOT_USERNAME = "medart_hub_bot"

bot = telebot.TeleBot(BOT_TOKEN)

# ഡാറ്റാബേസ് സെറ്റ് ചെയ്യൽ
def init_db():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            message_id INTEGER,
            photo_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# സബ്സ്ക്രിപ്ഷൻ ചെക്ക് ചെയ്യുന്ന ഭാഗം
def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(MAIN_CHANNEL_ID, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        print(f"Subscription Check Error: {e}")
        return False

# പ്രൈവറ്റ് ചാനലിൽ ഫയലോ പോസ്റ്ററോ വരുമ്പോൾ റീഡ് ചെയ്യുന്ന ഭാഗം
@bot.channel_post_handler(content_types=['document', 'video', 'photo'])
def handle_channel_post(message):
    if message.chat.id == PRIVATE_CHANNEL_ID:
        file_name = None
        photo_id = None

        # 1. പോസ്റ്റർ ഫോട്ടോ ആണെങ്കിൽ
        if message.content_type == 'photo':
            photo_id = message.photo[-1].file_id
            file_name = message.caption if message.caption else "New Movie"

        # 2. ഫയൽ അല്ലെങ്കിൽ വീഡിയോ ആണെങ്കിൽ
        elif message.document:
            file_name = message.document.file_name
        elif message.video:
            file_name = message.caption if message.caption else (message.video.file_name if message.video.file_name else "🍿 Movie File")

        if file_name:
            clean_name = file_name.replace('.mp4', '').replace('.mkv', '').replace('.', ' ').replace('@', ' ')
            
            conn = sqlite3.connect("movies.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO movies (file_name, message_id, photo_id) VALUES (?, ?, ?)", 
                           (clean_name.lower().strip(), message.message_id, photo_id))
            conn.commit()
            conn.close()
            print(f"🍿 Saved to Database: {clean_name}")
            
            # മെയിൻ ചാനലിലേക്ക് പ്രൊഫഷണൽ ഇംഗ്ലീഷ് പരസ്യം അയക്കുന്നു
            send_to_main_channel(clean_name, photo_id)

# മെയിൻ ചാനലിലേക്ക് പരസ്യം അയക്കുന്നു
def send_to_main_channel(movie_name, photo_id):
    try:
        bot_link = f"https://t.me/{BOT_USERNAME}?start=search"
        formatted_name = movie_name.title()
        
        caption_text = (
            f"🎬 **NEW MOVIE AVAILABLE** 🎬\n\n"
            f"🍿 **Movie Name:** {formatted_name}\n\n"
            f"👇 Click the download button below to get this movie instantly from our bot!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Provided By Levino*"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📥 Download From Bot", url=bot_link))
        
        if photo_id:
            bot.send_photo(MAIN_CHANNEL_ID, photo_id, caption=caption_text, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(MAIN_CHANNEL_ID, caption_text, reply_markup=markup, parse_mode="Markdown")
        print("📢 Professional English ad sent to Main Channel!")
    except Exception as e:
        print(f"Error sending ad to main channel: {e}")

# സ്റ്റാർട്ട് കമാൻഡ്
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    try:
        chat_info = bot.get_chat(MAIN_CHANNEL_ID)
        channel_url = chat_info.invite_link if chat_info.invite_link else f"https://t.me/{chat_info.username}"
    except:
        channel_url = "https://t.me/medart_hub"

    if not is_user_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Join Channel", url=channel_url))
        bot.reply_to(message, "⚠️ **Please join our main channel to get the file download link!**\n\nAfter joining, come back to the bot and search for your movie again.", reply_markup=markup)
        return

    welcome_text = (
        "🍿 **Welcome to Medart Hub Bot!** 🍿\n\n"
        "Type the movie name with correct spelling here to search...\n\n"
        "_*Bot Created By Levino*_"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# 2 മിനിറ്റിന് ശേഷം ഫയൽ തനിയെ ഡിലീറ്റ് ചെയ്യുന്ന ഫങ്ക്ഷൻ (Background Thread)
def auto_delete_file(chat_id, message_id):
    time.sleep(120)  # 120 സെക്കൻഡ് = 2 മിനിറ്റ്
    try:
        bot.delete_message(chat_id, message_id)
        print(f"🗑️ Copyright Auto-Deleted Message ID: {message_id}")
    except Exception as e:
        print(f"Failed to delete message: {e}")

# സെർച്ച് ചെയ്യുമ്പോൾ സിനിമ അയക്കുന്ന ഭാഗം
@bot.message_handler(func=lambda message: True)
def search_movie(message):
    user_id = message.from_user.id

    if not is_user_subscribed(user_id):
        return

    query = message.text.strip().lower()
    
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT message_id FROM movies WHERE file_name LIKE ?", (f"%{query}%",))
    results = cursor.fetchall()
    conn.close()
    
    if results:
        warning_msg = bot.reply_to(message, "🔍 **Movie found! Sending the file.**\n\n⚠️ _Note: This file will be automatically deleted after 2 minutes for copyright protection!_")
        
        for (msg_id,) in results:
            try:
                sent_file = bot.copy_message(chat_id=message.chat.id, from_chat_id=PRIVATE_CHANNEL_ID, message_id=msg_id)
                
                # ഫയലും വാർണിംഗ് മെസ്സേജും 2 മിനിറ്റിന് ശേഷം ഡിലീറ്റ് ആക്കാൻ ബാക്ക്ഗ്രൗണ്ടിലേക്ക് വിടുന്നു
                threading.Thread(target=auto_delete_file, args=(message.chat.id, sent_file.message_id)).start()
                threading.Thread(target=auto_delete_file, args=(message.chat.id, warning_msg.message_id)).start()
                
            except Exception as e:
                print(f"Error sending file: {e}")
    else:
        bot.reply_to(message, f"❌ Sorry, no movies found matching '{message.text}'!")

print("⚡ Medart Hub Bot is running successfully...")
bot.infinity_polling()