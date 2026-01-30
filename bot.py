import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

if not os.path.exists("downloads"):
    os.makedirs("downloads")

user_links = {}

CAPTION = "*POWERED BY:- @ANIME_TV_INDIA*\n*@@Video_Saver_MGbot*"

# ========== COOL PROGRESS BAR ==========
def progress_bar(percent):
    p = int(percent.replace('%','').strip())
    filled = int(p / 10)
    bar = "🟩" * filled + "⬜" * (10 - filled)
    return f"{bar} {percent}"

def progress_hook(d, msg):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%')
        speed = d.get('_speed_str', '')
        eta = d.get('_eta_str', '')
        try:
            msg.edit_text(
                f"📥 Downloading...\n{progress_bar(percent)}\n⚡ {speed} | ⏳ ETA {eta}"
            )
        except:
            pass

# ========== COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send video link\n\nCommands:\n"
        "/start - Start bot\n"
        "/help - Help\n"
        "/about - Bot info"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send any video link and choose quality 🎬")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ Advanced Video Saver Bot")

# ========== LINK ==========
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_links[update.message.chat_id] = url

    keyboard = [
        [InlineKeyboardButton("240p", callback_data="240"),
         InlineKeyboardButton("360p", callback_data="360")],
        [InlineKeyboardButton("480p", callback_data="480"),
         InlineKeyboardButton("720p 🚀", callback_data="720")],
        [InlineKeyboardButton("1080p", callback_data="1080")],
        [InlineKeyboardButton("🎵 MP3", callback_data="mp3")]
    ]

    await update.message.reply_text("Select format ⬇️",
        reply_markup=InlineKeyboardMarkup(keyboard))

# ========== DOWNLOAD ==========
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
