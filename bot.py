import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import asyncio

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ ERROR: BOT_TOKEN not set!")
    logger.error("Add BOT_TOKEN in Railway Variables")
    exit(1)

# Create downloads folder
os.makedirs("downloads", exist_ok=True)

class WorkingBot:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        await update.message.reply_text(
            "🤖 *Video Downloader Bot*\n\n"
            "Send me any video URL from:\n"
            "• YouTube\n• TikTok\n• Instagram\n• Facebook\n• Twitter\n• 1000+ sites\n\n"
            "⚡ Just send the URL!",
            parse_mode='Markdown'
        )
    
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video URL"""
        url = update.message.text.strip()
        
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text("❌ Send a valid URL starting with http:// or https://")
            return
        
        # Show processing
        msg = await update.message.reply_text("🔍 Checking video...")
        
        try:
            # Get video info
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Create buttons
                keyboard = [
                    [InlineKeyboardButton("🎬 Video", callback_data=f"video:{url}")],
                    [InlineKeyboardButton("🎵 Audio Only", callback_data=f"audio:{url}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send info
                await msg.edit_text(
                    f"📹 *Found!*\n\n"
                    f"**Title:** {info.get('title', 'Unknown')}\n"
                    f"**Duration:** {info.get('duration', 0)}s\n"
                    f"**Uploader:** {info.get('uploader', 'Unknown')}\n\n"
                    f"Select download type:",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("video:"):
            url = data.split(":", 1)[1]
            await self.download_video(query, url)
        
        elif data.startswith("audio:"):
            url = data.split(":", 1)[1]
            await self.download_audio(query, url)
    
    async def download_video(self, query, url: str):
        """Download video"""
        msg = await query.message.reply_text("⏬ Downloading video...")
        
        try:
            ydl_opts = {
                'format': 'best[filesize<50M]',  # Limit to 50MB for Telegram
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Check file size
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    
                    if file_size > 50 * 1024 * 1024:  # 50MB
                        os.remove(filename)
                        await msg.edit_text("❌ File too large (>50MB). Try shorter video.")
                        return
                    
                    await msg.edit_text("📤 Uploading...")
                    
                    # Send video
                    with open(filename, 'rb') as f:
                        await query.message.reply_video(
                            video=f,
                            caption=f"✅ {info.get('title', 'Video')}",
                            supports_streaming=True
                        )
                    
                    await msg.delete()
                    os.remove(filename)
                else:
                    await msg.edit_text("❌ Download failed. File not created.")
                    
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")
    
    async def download_audio(self, query, url: str):
        """Download audio"""
        msg = await query.message.reply_text("🎵 Extracting audio...")
        
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                filename = filename.rsplit('.', 1)[0] + '.mp3'
                
                if os.path.exists(filename):
                    await msg.edit_text("📤 Uploading audio...")
                    
                    with open(filename, 'rb') as f:
                        await query.message.reply_audio(
                            audio=f,
                            caption=f"🎵 {info.get('title', 'Audio')}"
                        )
                    
                    await msg.delete()
                    os.remove(filename)
                else:
                    await msg.edit_text("❌ Audio extraction failed")
                    
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")

def main():
    """Start bot - FIXED for Railway"""
    print("🚀 Starting Video Downloader Bot...")
    print(f"✅ Token: {BOT_TOKEN[:10]}...")
    
    # Create application with persistence disabled
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Initialize bot
    bot = WorkingBot()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_url))
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    
    # Start bot with proper settings for Railway
    print("🤖 Bot is ready on Railway!")
    application.run_polling(
        drop_pending_updates=True,
        close_loop=False  # Important for Railway
    )

if __name__ == '__main__':
    main()    • Progress indicators
    • Support for 1000+ sites
    
    *Note:* Some sites may have restrictions.
    """
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages containing URLs."""
    message_text = update.message.text
    
    # Check if message contains URL
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .\-?=&%]*'
    urls = re.findall(url_pattern, message_text)
    
    if not urls:
        await update.message.reply_text("Please send me a valid video URL!")
        return
    
    url = urls[0]
    
    # Get video info
    try:
        await update.message.reply_text("🔍 Fetching video information...")
        
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check if it's a playlist
            if 'entries' in info:
                await update.message.reply_text("⚠️ Playlists are not supported. Please send a single video URL.")
                return
            
            # Create quality/format selection keyboard
            keyboard = []
            
            # Audio only option
            keyboard.append([InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data=f"format_{url}_audio")])
            
            # Video quality options
            if 'formats' in info:
                formats = info['formats']
                # Filter video formats
                video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                
                # Get unique resolutions
                resolutions = {}
                for fmt in video_formats:
                    res = fmt.get('resolution', 'N/A')
                    if res != 'N/A' and res not in resolutions:
                        resolutions[res] = fmt
                
                # Add quality options (limit to 5)
                for i, (res, fmt) in enumerate(list(resolutions.items())[:5]):
                    keyboard.append([
                        InlineKeyboardButton(f"📹 Video {res}", 
                         callback_data=f"format_{url}_video_{fmt['format_id']}")
                    ])
            
            # Add best quality option
            keyboard.append([
                InlineKeyboardButton("🏆 Best Quality", 
                 callback_data=f"format_{url}_best")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send video info with options
            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0)
            duration_str = f"{duration//60}:{duration%60:02d}" if duration else "Unknown"
            
            caption = f"""
            *📹 Video Found!*
            
            *Title:* {title}
            *Duration:* {duration_str}
            
            Select download option:
            """
            
            await update.message.reply_text(
                caption,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
    except Exception as e:
        logger.error(f"Error fetching video info: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("format_"):
        parts = data.split("_")
        url = parts[1]
        format_type = parts[2]
        
        user_id = query.from_user.id
        user_data[user_id] = {
            'url': url,
            'format': format_type,
            'message': query.message
        }
        
        # Start download
        await download_video(update, context)

async def progress_hook(d, update, context):
    """Progress hook for download."""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%').strip()
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        
        # Update progress message
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=update.effective_message.message_id + 1,
                text=f"⬇️ Downloading...\nProgress: {percent}\nSpeed: {speed}\nETA: {eta}"
            )
        except:
            pass
            
    elif d['status'] == 'finished':
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=update.effective_message.message_id + 1,
                text="✅ Download complete!\n⏫ Uploading to Telegram..."
            )
        except:
            pass

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download and send video."""
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in user_data:
        await query.edit_message_text("Session expired. Please send the URL again.")
        return
    
    data = user_data[user_id]
    url = data['url']
    format_type = data['format']
    
    await query.edit_message_text("⏳ Processing your request...")
    
    # Create progress message
    progress_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🔄 Starting download..."
    )
    
    try:
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                'progress_hooks': [lambda d: asyncio.create_task(progress_hook(d, update, context))],
                'quiet': True,
            }
            
            if format_type == 'audio':
                # Audio only download
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
                await progress_msg.edit_text("🎵 Extracting audio...")
                
            elif format_type == 'best':
                # Best quality
                ydl_opts['format'] = 'best'
                
            elif format_type.startswith('video'):
                # Specific video format
                format_id = format_type.split('_')[1]
                ydl_opts['format'] = format_id
            
            # Download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Adjust filename for audio
                if format_type == 'audio':
                    filename = os.path.splitext(filename)[0] + '.mp3'
            
            # Send file
            await progress_msg.edit_text("📤 Uploading to Telegram...")
            
            with open(filename, 'rb') as file:
                if format_type == 'audio':
                    await context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=file,
                        title=info.get('title', 'Audio'),
                        performer=info.get('uploader', 'Unknown'),
                        caption="🎵 Converted to audio by Video Downloader Bot"
                    )
                else:
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=file,
                        caption="📹 Downloaded by Video Downloader Bot",
                        supports_streaming=True
                    )
            
            # Cleanup
            await progress_msg.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="✅ Done! Send another URL or use /start"
            )
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        await progress_msg.edit_text(f"❌ Error: {str(e)}")
    
    finally:
        # Clean user data
        if user_id in user_data:
            del user_data[user_id]

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_error_handler(error_handler)
    
    # Start the bot
    if WEBHOOK_URL:
        # Webhook mode for production
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
        )
    else:
        # Polling mode for development
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
