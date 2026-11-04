Start 
import telebot
from telebot import types
import hashlib
from flask import Flask, request
import threading

# --- SOZLAMALAR ---
TOKEN = "SIZNING_TELEGRAM_BOT_TOKENINGIZ"  # @BotFather dan olingan token
APP_ID = "SIZNING_APP_ID" # CPX Research dan olingan App ID
SECURE_HASH = "SIZNING_SECURE_HASH" # CPX Research dan olingan Secure Hash

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- TELEGRAM BOT QISMI ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text="📝 So'rovnoma to'ldirish (Pul ishlash)", callback_data="get_survey")
    markup.add(btn)
    bot.send_message(message.chat.id, "Salom! Pul ishlash uchun quyidagi tugmani bosing.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "get_survey")
def send_survey(call):
    user_id = call.from_user.id
    
    # CPX uchun xavfsizlik kodi
    hash_string = f"{user_id}-{SECURE_HASH}"
    hash_hex = hashlib.md5(hash_string.encode()).hexdigest()
    
    # CPX havolasi
    cpx_link = f"https://offers.cpx-research.com/index.php?app_id={APP_ID}&ext_user_id={user_id}&secure_hash={hash_hex}"
    
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text="So'rovnomani boshlash", url=cpx_link)
    markup.add(btn)
    
    bot.send_message(call.message.chat.id, "Quyidagi havolani bosib so'rovnomani to'ldiring:", reply_markup=markup)

# --- FLASK SERVER QISMI (CPX POSTBACK UCHUN) ---
@app.route('/postback', methods=['GET'])
def postback():
    user_id = request.args.get('user_id')
    amount = request.args.get('amount')
    status = request.args.get('status')
    
    if status == '1':  # Agar so'rovnoma muvaffaqiyatli tugagan bo'lsa
        # Foydalanuvchiga xabar yuborish
        try:
            bot.send_message(user_id, f"Tabriklaymiz! Siz {amount} so'm topdingiz! 💰")
            # Bu yerda foydalanuvchining ma'lumotlar bazasidagi balansiga pul qo'shishingiz mumkin
        except Exception as e:
            print(f"Xatolik: {e}")
            
    return "OK", 200

# --- ISHGA TUSHIRISH ---
def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    # Flask serverini alohida thread'da ishga tushirish
    threading.Thread(target=run_flask).start()
    # Botni ishga tushirish
    bot.polling(none_stop=True)
