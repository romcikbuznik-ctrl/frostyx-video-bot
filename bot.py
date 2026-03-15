import os
import telebot
import yt_dlp
from telebot import types
import time
from dotenv import load_dotenv

STATS_FILE = "stats.txt"

# Дані спонсора
SPONSOR_LINK = "https://t.me/BroStarsFree_bot?start=1906858193"
SPONSOR_USERNAME = "УТЯСТАР"  # Виправив юзернейм (без пробілу)

# Словник для зберігання верифікованих користувачів
verified_users = {}

# створюємо файл статистики якщо його нема
if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w") as f:
        f.write("0")

def add_stat():
    with open(STATS_FILE, "r") as f:
        count = int(f.read())
    count += 1
    with open(STATS_FILE, "w") as f:
        f.write(str(count))

# Вставляємо токен безпосередньо
BOT_TOKEN = "8778468314:AAGum9ugqZ_Xp0NloYxHeH9FvvWGZ_VwYFE"

bot = telebot.TeleBot(BOT_TOKEN)

# Словник для налаштувань yt-dlp
ydl_opts = {
    'format': 'best[height<=1080]',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'quiet': True,
}

# Функція перевірки чи користувач верифікований
def is_user_verified(user_id):
    return verified_users.get(user_id, False)

# Функція для відправки повідомлення про необхідність підписки
def send_subscription_required(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    text = (
        f"👋 Привет, {user_name}!\n\n"
        f"❌ <b>Доступ запрещен!</b>\n\n"
        f"🤝 Для использования бота необходимо выполнить задания нашего спонсора:\n"
        f"📌 Нажми кнопку ниже, перейди к спонсору и выполни там задания, а затем нажми 'Я выполнил ✅'"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    sponsor_btn = types.InlineKeyboardButton(
        "🤟 ПЕРЕЙТИ К СПОНСОРУ 🤟", 
        url=SPONSOR_LINK
    )
    
    confirm_btn = types.InlineKeyboardButton(
        "✅ Я ВЫПОЛНИЛ ✅", 
        callback_data="confirm_subscription"
    )
    
    markup.add(sponsor_btn, confirm_btn)
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup,
        parse_mode='HTML'
    )

# Обробка callback-ів від кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    
    if call.data == "confirm_subscription":
        verified_users[user_id] = True
        
        bot.answer_callback_query(
            call.id, 
            "✅ Подписка подтверждена! Теперь вы можете пользоваться ботом.", 
            show_alert=True
        )
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        welcome_text = (
            "🎉 <b>Задание выполнено!</b>\n\n"
            "Теперь вы можете скачивать видео с YouTube, TikTok и Instagram!\n\n"
            "📥 Просто отправьте мне ссылку на видео."
        )
        bot.send_message(call.message.chat.id, welcome_text, parse_mode='HTML')

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if is_user_verified(user_id):
        bot.reply_to(
            message, 
            "Привет! Пришли мне ссылку с видео с YouTube, TikTok или Instagram и я скачаю его без водяного знака! 📥"
        )
    else:
        send_subscription_required(message)

# Команда /reset (для тестування)
@bot.message_handler(commands=['reset'])
def reset_subscription(message):
    user_id = message.from_user.id
    if user_id in verified_users:
        del verified_users[user_id]
        bot.reply_to(message, "🔄 Статус підписки скинуто. Натисніть /start для повторної перевірки.")
    else:
        bot.reply_to(message, "Ви ще не були підписані.")

# 👇 НОВИЙ ОБРОБНИК ДЛЯ ЦИФР 4321 (статистика)
@bot.message_handler(func=lambda message: message.text == "4321")
def show_stats_by_code(message):
    user_id = message.from_user.id
    
    # Перевіряємо підписку
    if not is_user_verified(user_id):
        send_subscription_required(message)
        return
    
    # Отримуємо статистику
    with open(STATS_FILE, "r") as f:
        count = f.read()
    
    # Створюємо гарне повідомлення зі статистикою
    stats_text = (
        "📊 <b>СЕКРЕТНА СТАТИСТИКА</b> 📊\n\n"
        f"🔢 <b>Код доступу:</b> 4321\n"
        f"📥 <b>Всього скачано відео:</b> {count}\n"
        f"🤖 <b>Бот:</b> @Frostyyx45Bot\n"
        f"👤 <b>Користувач:</b> {message.from_user.first_name}\n\n"
        f"📅 <b>Дата:</b> {time.strftime('%d.%m.%Y %H:%M')}"
    )
    
    # Відправляємо статистику
    bot.reply_to(message, stats_text, parse_mode='HTML')
    
    # Додатково створюємо файл звіту (як було раніше)
    report_text = f"""Статистика FrostyxSaveBot
=========================
Всього скачано відео: {count}
Користувач: {message.from_user.first_name} (@{message.from_user.username})
ID: {message.from_user.id}
Дата: {time.strftime('%d.%m.%Y %H:%M')}
    """
    
    with open(f"stats_{user_id}.txt", "w", encoding="utf-8") as f:
        f.write(report_text)
    
    with open(f"stats_{user_id}.txt", "rb") as f:
        bot.send_document(message.chat.id, f, caption="📊 Детальний звіт")
    
    os.remove(f"stats_{user_id}.txt")

# Обробка всіх текстових повідомлень (посилань на відео)
@bot.message_handler(func=lambda msg: not msg.text.startswith("/") and msg.text != "4321")
def download_video(message):
    user_id = message.from_user.id
    
    if not is_user_verified(user_id):
        send_subscription_required(message)
        return

    add_stat()

    url = message.text.strip()
    chat_id = message.chat.id

    if not url.startswith('http'):
        bot.reply_to(message, "Пожалуйста, пришли мне правильную ссылку.")
        return

    status_msg = bot.reply_to(message, "⏳ Скачиваю видео...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Шукаємо файл
            actual_file = None
            for file in os.listdir('downloads'):
                if file.startswith(info['title'][:50]):
                    actual_file = os.path.join('downloads', file)
                    break
            
            if actual_file and os.path.exists(actual_file):
                with open(actual_file, 'rb') as video_file:
                    bot.send_video(
                        chat_id, 
                        video_file, 
                        caption=f"📥 Скачано из \n🤖 @Frostyyx45Bot",
                        timeout=500
                    )
                
                os.remove(actual_file)
                bot.delete_message(chat_id, status_msg.message_id)
            else:
                bot.edit_message_text(
                    "❌ Не удалось найти скачанный файл", 
                    chat_id, 
                    status_msg.message_id
                )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка: {str(e)[:200]}", 
            chat_id, 
            status_msg.message_id
        )

# Запускаємо бота
if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)
    
    print("🤖 Бот запускається...")
    print(f"🤝 Спонсор: @{SPONSOR_USERNAME}")
    print("✅ Система підписки активна!")
    print("🔐 Секретний код статистики: 4321")
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook видалено")
    except:
        pass
    
    try:
        bot.infinity_polling(timeout=60)
    except Exception as e:
        print(f"❌ Помилка: {e}")
        time.sleep(3)
        bot.infinity_polling(timeout=60)
