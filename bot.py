import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send video link 🎬")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    msg = await update.message.reply_text("Downloading... ⏬")

    ydl_opts = {
        'format': 'bv*+ba/b',
        'outtmpl': 'video.%(ext)s',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)
            file_name = file_name.rsplit(".", 1)[0] + ".mp4"

        await update.message.reply_video(video=open(file_name, 'rb'))
        os.remove(file_name)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"Error ❌ {e}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

app.run_polling()
