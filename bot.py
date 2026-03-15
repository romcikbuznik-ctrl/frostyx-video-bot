import os
import telebot
import yt_dlp
from dotenv import load_dotenv

STATS_FILE = "stats.txt"

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

# Завантажуємо токен з .env файлу (але ми вже вставили його прямо в код)
# load_dotenv()
# BOT_TOKEN = os.getenv('BOT_TOKEN')

# Вставляємо токен безпосередньо (ви можете використовувати цей варіант)
BOT_TOKEN = "8778468314:AAGum9ugqZ_Xp0NloYxHeH9FvvWGZ_VwYFE"

bot = telebot.TeleBot(BOT_TOKEN)

# Словник для налаштувань yt-dlp
ydl_opts = {
    'format': 'best[height<=1080]',  # Найкраще відео до 720p
    'outtmpl': 'downloads/%(title)s.%(ext)s',  # Куди зберігати
    'quiet': True,
}

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Пришли мне ссылку с видео с YouTube, TikTok или Instagram и я скачаю его без водяного знака!.")

# Обробка всіх текстових повідомлень
@bot.message_handler(func=lambda msg: not msg.text.startswith("/"))
def download_video(message):

    add_stat()

    url = message.text.strip()
    chat_id = message.chat.id

    # Перевіряємо, чи це схоже на посилання
    if not url.startswith('http'):
        bot.reply_to(message, "Пожалуйста, пришли мне правильную ссылку.")
        return

    # Повідомляємо про початок завантаження
    bot.reply_to(message, "⏳ Скачиваю видео...")

    try:
        # Завантажуємо відео за допомогою yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            # Перевіряємо, яке розширення файлу (може бути .mkv, .webm тощо)
            # Тут потрібна логіка для пошуку фактично завантаженого файлу
            # Для спрощення припустимо, що ми знаємо назву
            video_file = open(file_path, 'rb')
            bot.send_video(chat_id, video_file, caption=info.get('information  ', 'Скачено из @Frostyyx45Bot' ), timeout=500)
            video_file.close()

            # Видаляємо файл після відправки
            os.remove(file_path)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# Запускаємо бота
if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)  # Створюємо папку для завантажень
    print("Бот запущено...")


    @bot.message_handler(commands=["stats"])
    def send_stats(message):
        with open(STATS_FILE, "r") as f:
            count = f.read()

        text = f"""📊 Статистика FrostyxSaveBot

    Кличество скачанных видео: {count}
    """

        with open("report.txt", "w", encoding="utf-8") as f:
            f.write(text)

        with open("report.txt", "rb") as f:
            bot.send_document(message.chat.id, f)
    bot.infinity_polling()
