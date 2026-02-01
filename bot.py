import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send video link 🎬")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    msg = await update.message.reply_text("Downloading... ⏬")

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'video.%(ext)s',
        'merge_output_format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
        },
        'quiet': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)
            if not file_name.endswith(".mp4"):
                file_name = file_name.rsplit(".", 1)[0] + ".mp4"

        await update.message.reply_video(video=open(file_name, 'rb'))
        os.remove(file_name)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"Error ❌ {e}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

app.run_polling()# ========== DOWNLOAD ==========
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    url = user_links.get(chat_id)
    msg = await query.message.reply_text("⏳ Preparing...")

    choice = query.data

    try:
        if choice == "mp3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
                'progress_hooks': [lambda d: progress_hook(d, msg)],
                'http_headers': {'User-Agent': 'Mozilla/5.0'}
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"

            await msg.edit_text("📤 Uploading audio...")
            await query.message.reply_audio(audio=open(file_path, 'rb'),
                                            caption=CAPTION,
                                            parse_mode="Markdown")
            os.remove(file_path)

        else:
            ydl_opts = {
                'format': f'bestvideo[height<={choice}]+bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'merge_output_format': 'mp4',
                'progress_hooks': [lambda d: progress_hook(d, msg)],
                'http_headers': {'User-Agent': 'Mozilla/5.0'}
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            await msg.edit_text("📤 Uploading video...")
            await query.message.reply_video(video=open(file_path, 'rb'),
                                            caption=CAPTION,
                                            parse_mode="Markdown")
            os.remove(file_path)

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"Error ❌ {e}")

# ========== MAIN ==========
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("about", about))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(download_callback))

print("Bot Running...")
app.run_polling()
