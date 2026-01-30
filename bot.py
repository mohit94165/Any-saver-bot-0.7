import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

if not os.path.exists("downloads"):
    os.makedirs("downloads")

# ========== VIDEO DOWNLOAD ==========
def download_video(url):
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'best',
        'noplaylist': True,
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# ========== AUDIO DOWNLOAD ==========
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Link bhej bhai 🎬🎵🖼️")

# ========== HANDLE MESSAGE ==========
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("Downloading... ⏳")

    try:
        # Image
        if url.endswith((".jpg", ".png", ".jpeg", ".webp")):
            await update.message.reply_photo(photo=url)
            return

        # Audio
        if "audio" in url or "mp3" in url:
            file_path = download_audio(url)
            await update.message.reply_audio(audio=open(file_path, 'rb'))
            os.remove(file_path)
            return

        # Video
        file_path = download_video(url)
        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(f"Error ❌ {e}")

# ========== MAIN ==========
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

print("Bot Running...")
app.run_polling()
