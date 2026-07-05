import telebot
import os
import threading
import time

# ടോക്കൺ എൻവയോൺമെന്റിൽ നിന്ന് എടുക്കുന്നു
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# ചാനൽ ഐഡികൾ ഇവിടെ നൽകുക (ഉദാഹരണത്തിന്: -100123456789)
MAIN_CHANNEL_ID = -1004469439263 
PRIVATE_CHANNEL_ID = -1004307986554

# ഫൂട്ടർ മെസ്സേജ്
FOOTER = "\n\nPowered by Levino"

def is_user_joined(user_id):
    try:
        member = bot.get_chat_member(MAIN_CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# പ്രൈവറ്റ് ചാനലിൽ ഫയൽ വരുമ്പോൾ മെയിൻ ചാനലിലേക്ക് പോസ്റ്റ് ചെയ്യുന്നു
@bot.channel_post_handler(chat_types=['channel'], func=lambda message: message.chat.id == PRIVATE_CHANNEL_ID)
def forward_to_main(message):
    caption = message.caption if message.caption else "പുതിയ സിനിമ വന്നിരിക്കുന്നു!"
    post_text = f"{caption}\n\nസിനിമ ഡൗൺലോഡ് ചെയ്യാൻ താഴെ ലിങ്കിൽ ക്ലിക്ക് ചെയ്യുക:\nhttps://t.me/{bot.get_me().username}?start={message.message_id}{FOOTER}"
    bot.send_message(MAIN_CHANNEL_ID, post_text)

# സ്റ്റാർട്ട് കമാൻഡ് (ജോയിൻ ചെക്ക്)
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_user_joined(user_id):
        bot.reply_to(message, f"ആദ്യം മെയിൻ ചാനലിൽ ജോയിൻ ചെയ്യൂ!{FOOTER}")
        return

    # ഫയൽ ഉണ്ടെങ്കിൽ അയക്കുന്നു
    try:
        file_id = message.text.split(' ')[1]
        sent_msg = bot.copy_message(chat_id=message.chat.id, from_chat_id=PRIVATE_CHANNEL_ID, message_id=int(file_id))
        
        # 2 മിനിറ്റിന് ശേഷം ഡിലീറ്റ് ചെയ്യാൻ
        threading.Timer(120, lambda: bot.delete_message(message.chat.id, sent_msg.message_id)).start()
        
    except:
        bot.reply_to(message, f"ക്ഷമിക്കണം, ഫയൽ ലഭ്യമല്ല.{FOOTER}")

bot.infinity_polling()