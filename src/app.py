import telebot
from telebot import types
import sqlite3

# --- SOZLAMALAR ---
TOKEN = "8737262292:AAHd9AoCJuf7ugQygLwO18YXu0xNRGUA6a4"
MONETAG_LINK = "https://uplcm.com/4/12191182" 
ADMIN_ID = 123456789  # BU YERGA O'ZINGIZNING TELEGRAM ID RAQAMINGIZNI YOZING!

bot = telebot.TeleBot(TOKEN)

# --- MA'LUMOTLAR BAZASI ---
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, jcoin REAL DEFAULT 0.0, referals INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        user = (user_id, 0, 0.0, 0)
    conn.close()
    return user

def update_balance(user_id, amount):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
    conn.commit()
    conn.close()

# --- BOT QISMI ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    # Referal tizimi (agar havola orqali kirgan bo'lsa)
    if len(message.text.split()) > 1:
        referrer_id = int(message.text.split()[1])
        if referrer_id != user_id:
            update_balance(referrer_id, 200) # Referal uchun 200 so'm
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET referals = referals + 1 WHERE id=?", (referrer_id,))
            conn.commit()
            conn.close()
            try:
                bot.send_message(referrer_id, "🎉 Yangi do'stingiz qo'shildi! Siz 200 so'm oldingiz!")
            except:
                pass

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("💰 Pul ishlash")
    btn2 = types.KeyboardButton("💳 Balansim")
    btn3 = types.KeyboardButton("👥 Do'st taklif qilish")
    btn4 = types.KeyboardButton("🏦 Pul yechish")
    markup.add(btn1, btn2, btn3, btn4)
    
    text = (
        f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
        "Botimizga xush kelibsiz.\n\n"
        "💰 Pul ishlash, J Coin yig'ish va o'yinlar uchun almaz olish uchun quyidagi menyudan foydalaning."
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "💰 Pul ishlash")
def handle_earn(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text="📺 Reklamani ko'rish (+500 so'm)", url=MONETAG_LINK)
    markup.add(btn)
    bot.send_message(message.chat.id, "Reklamani ko'ring va balansingizga 500 so'm qo'shing:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "💳 Balansim")
def handle_balance(message):
    user = get_user(message.from_user.id)
    text = (
        f"💳 **Sizning hisobingiz:**\n\n"
        f"💰 Balans: {user[1]} so'm\n"
        f"🪙 J Coin: {user[2]} (1 J Coin = 1000 so'm)\n"
        f"👥 Taklif qilganlar: {user[3]} ta"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "👥 Do'st taklif qilish")
def handle_referal(message):
    bot_info = bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    text = (
        f"👥 **Do'stlaringizni taklif qiling!**\n\n"
        f"Har bir taklif qilgan do'stingiz uchun **200 so'm** olasiz!\n\n"
        f"Sizning havolangiz:\n`{link}`"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🏦 Pul yechish")
def handle_withdraw(message):
    bot.send_message(message.chat.id, "Qancha so'm yechib olmoqchisiz? (Faqat raqam kiriting, masalan: 5000)")
    bot.register_next_step_handler(message, process_withdraw)

def process_withdraw(message):
    try:
        amount = int(message.text)
        user = get_user(message.from_user.id)
        if amount > user[1]:
            bot.send_message(message.chat.id, "❌ Balansingizda yetarli pul yo'q!")
            return
        
        # Adminga xabar yuborish
        admin_text = (
            f"🚨 **YANGI PUL YECHISH SO'ROVI!**\n\n"
            f"👤 Foydalanuvchi: {message.from_user.first_name}\n"
            f"🆔 ID: {message.from_user.id}\n"
            f"💰 Summa: {amount} so'm\n\n"
            f"Tasdiqlash uchun: /tasdiqla {message.from_user.id} {amount}"
        )
        bot.send_message(ADMIN_ID, admin_text, parse_mode='Markdown')
        bot.send_message(message.chat.id, "✅ So'rovingiz adminga yuborildi. Tez orada ko'rib chiqiladi.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Iltimos, faqat raqam kiriting.")

# --- ADMIN BUYRUQLARI ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    
    text = (
        f"👑 **Admin Panel**\n\n"
        f"👥 Jami foydalanuvchilar: {total_users} ta\n\n"
        f"Buyruqlar:\n"
        f"/users - Foydalanuvchilar ro'yxati\n"
        f"/tasdiqla [id] [summa] - Pul yechishni tasdiqlash"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, balance FROM users")
    users = cursor.fetchall()
    conn.close()
    
    text = "👥 **Foydalanuvchilar ro'yxati:**\n\n"
    for u in users:
        text += f"🆔 {u[0]} | Balans: {u[1]} so'm\n"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['tasdiqla'])
def approve_withdraw(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        amount = int(parts[2])
        
        update_balance(user_id, -amount) # Pulni ayirish
        bot.send_message(user_id, f"✅ Sizning {amount} so'm pul yechish so'rovingiz tasdiqlandi!")
        bot.send_message(message.chat.id, f"✅ Foydalanuvchi {user_id} ga {amount} so'm yuborildi.")
    except:
        bot.send_message(message.chat.id, "❌ Xatolik. Format: /tasdiqla [id] [summa]")

print("Bot ishga tushdi...")
bot.polling(none_stop=True)
