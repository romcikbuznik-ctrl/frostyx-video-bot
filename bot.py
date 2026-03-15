import os
import telebot
import yt_dlp
from telebot import types
import time
from dotenv import load_dotenv

STATS_FILE = "stats.txt"

# Дані спонсора
SPONSOR_LINK = "https://t.me/BroStarsFree_bot?start=1906858193"
SPONSOR_USERNAME = "УТЯ STAR"

# Словник для зберігання верифікованих користувачів
# У реальному проекті краще використовувати базу даних
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
    
    # Текст російською мовою
    text = (
        f"👋 Привет, {user_name}!\n\n"
        f"❌ <b>Доступ запрещен!</b>\n\n"
        f"🤝 Для использования бота необходимо выполнить задания нашего спонсора:\n"
        f"👉 @{SPONSOR_USERNAME}\n\n"
        f"📌 Нажми кнопку ниже, перейди к спонсору и выполни там задаия, а затем нажми 'Я выполнил ✅'"
    )
    
    # Створюємо кнопки
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Кнопка переходу до спонсора
    sponsor_btn = types.InlineKeyboardButton(
        "🤟 ПЕРЕЙТИ К СПОНСОРУ 🤟", 
        url=SPONSOR_LINK
    )
    
    # Кнопка підтвердження
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
        # Користувач підтверджує підписку
        verified_users[user_id] = True
        
        # Відповідаємо на callback
        bot.answer_callback_query(
            call.id, 
            "✅ Подписка подтверждена! Теперь вы можете пользоваться ботом.", 
            show_alert=True
        )
        
        # Видаляємо старе повідомлення
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        # Відправляємо привітання
        welcome_text = (
            "🎉 <b> Задание выполнено!</b>\n\n"
            "Теперь вы можете скачивать видео с YouTube, TikTok и Instagram!\n\n"
            "📥 Просто отправьте мне ссылку на видео."
        )
        bot.send_message(call.message.chat.id, welcome_text, parse_mode='HTML')
        
        # Показуємо статистику використання

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # Перевіряємо чи користувач верифікований
    if is_user_verified(user_id):
        bot.reply_to(
            message, 
            "Привет! Пришли мне ссылку с видео с YouTube, TikTok или Instagram и я скачаю его без водяного знака! 📥"
        )

# Команда /stats (доступна тільки після підписки)
@bot.message_handler(commands=['stats'])
def send_stats(message):
    user_id = message.from_user.id
    
    if not is_user_verified(user_id):
        send_subscription_required(message)
        return
    
    with open(STATS_FILE, "r") as f:
        count = f.read()

    text = f"""📊 <b>Статистика FrostyxSaveBot</b>

Количество скачанных видео: {count}
"""

    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(text)

    with open("report.txt", "rb") as f:
        bot.send_document(message.chat.id, f, caption="📊 Статистика бота")
    
    # Видаляємо файл після відправки
    os.remove("report.txt")

# Команда /reset (для тестування - скидає статус підписки)
@bot.message_handler(commands=['reset'])
def reset_subscription(message):
    user_id = message.from_user.id
    if user_id in verified_users:
        del verified_users[user_id]
        bot.reply_to(message, "🔄 Статус підписки скинуто. Натисніть /start для повторної перевірки.")
    else:
        bot.reply_to(message, "Ви ще не були підписані.")

# Обробка всіх текстових повідомлень (посилань на відео)
@bot.message_handler(func=lambda msg: not msg.text.startswith("/"))
def download_video(message):
    user_id = message.from_user.id
    
    # ПЕРЕВІРКА ПІДПИСКИ - найголовніше!
    if not is_user_verified(user_id):
        # Якщо не підписаний - показуємо повідомлення з кнопками
        send_subscription_required(message)
        return

    # Якщо підписаний - продовжуємо завантаження
    add_stat()

    url = message.text.strip()
    chat_id = message.chat.id

    # Перевіряємо, чи це схоже на посилання
    if not url.startswith('http'):
        bot.reply_to(message, "Пожалуйста, пришли мне правильную ссылку.")
        return

    # Повідомляємо про початок завантаження
    status_msg = bot.reply_to(message, "⏳ Скачиваю видео...")

    try:
        # Завантажуємо відео за допомогою yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # Шукаємо фактичний файл (може мати інше розширення)
            actual_file = None
            for file in os.listdir('downloads'):
                if file.startswith(info['title'][:50]):  # Порівнюємо початок назви
                    actual_file = os.path.join('downloads', file)
                    break
            
            if actual_file and os.path.exists(actual_file):
                # Відправляємо відео
                with open(actual_file, 'rb') as video_file:
                    bot.send_video(
                        chat_id, 
                        video_file, 
                        caption=f"📥 Скачано из @{message.from_user.username}\n🤖 @Frostyyx45Bot",
                        timeout=500
                    )
                
                # Видаляємо файл
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
    # Створюємо папку для завантажень
    os.makedirs('downloads', exist_ok=True)
    
    print("🤖 Бот запускається...")
    print(f"🤝 Спонсор: @{SPONSOR_USERNAME}")
    print("✅ Система підписки активна!")
    
    # Видаляємо webhook
    try:
        bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook видалено")
    except:
        pass
    
    # Запускаємо бота
    try:
        bot.infinity_polling(timeout=60)
    except Exception as e:
        print(f"❌ Помилка: {e}")
        time.sleep(3)
        bot.infinity_polling(timeout=60)
