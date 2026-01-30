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
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'en-US,en;q=0.9',
        }
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
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send link 🎬 (video) 🎵 (audio) 🖼️ (image)")

# ========== HANDLE LINK ==========
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("Downloading... ⏳")

    try:
        # IMAGE
        if url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            await update.message.reply_photo(photo=url)
            return

        # AUDIO REQUEST
        if "audio" in url or "mp3" in url:
            file_path = download_audio(url)
            await update.message.reply_audio(audio=open(file_path, 'rb'))
            os.remove(file_path)
            return

        # VIDEO DEFAULT
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
