# (c) Fasihi-Rad - Clean start_help.py plugin
import logging
from pyrogram import filters, Client
from pyrogram.types import Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from pyrogram.enums import ChatMemberStatus

from Adarsh.bot import StreamBot
from Adarsh.utils.database import Database
from Adarsh.utils.human_readable import byte_to_human_read
from Adarsh.vars import Var

logger = logging.getLogger(__name__)
db = Database(Var.DATABASE_URL, Var.NAME)

logger.info("🔌 start_help.py plugin loaded successfully")

buttonz = ReplyKeyboardMarkup(
    [
        ["Start⚡️", "Help📚", "Login🔑", "DC"],
        ["Support❤️", "Ping📡", "Status📊", "Maintainers😎"]
    ],
    resize_keyboard=True
)


@StreamBot.on_message((filters.command("start") | filters.regex('Start⚡️')) & filters.private)
async def start_handler(client: Client, message: Message) -> None:
    """Handle /start command and Start button"""
    logger.info(f"🚀 START: Command received from user {message.from_user.id} (@{message.from_user.username})")
    
    try:
        # Add user to database
        if not await db.is_user_exist(message.from_user.id):
            logger.info(f"👤 Adding new user: {message.from_user.id}")
            await db.add_user(
                message.from_user.id, 
                message.from_user.first_name, 
                message.from_user.last_name, 
                message.from_user.username
            )
            
            try:
                await client.send_message(
                    Var.BIN_CHANNEL,
                    f"**New User Joined:**\n\n"
                    f"Name: [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n"
                    f"Username: @{message.from_user.username}\n"
                    f"User ID: `{message.from_user.id}`"
                )
                logger.info("📢 Sent new user notification")
            except Exception as e:
                logger.error(f"❌ Failed to send new user notification: {e}")
                
    except Exception as e:
        logger.error(f"❌ Database error: {e}")

    # Check channel subscription if required  
    if hasattr(Var, 'UPDATES_CHANNEL') and Var.UPDATES_CHANNEL and Var.UPDATES_CHANNEL != "None":
        try:
            member = await client.get_chat_member(Var.UPDATES_CHANNEL, message.chat.id)
            if member.status == ChatMemberStatus.BANNED:
                await message.reply_text("❌ You are banned from using this bot.")
                return
                
        except UserNotParticipant:
            await message.reply_photo(
                photo="https://telegra.ph/file/9d94fc0af81234943e1a9.jpg",
                caption="**Please join our channel to use this bot! 🔐**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join Channel 🔓", url=f"https://t.me/{Var.UPDATES_CHANNEL}")]
                ])
            )
            return
            
        except Exception as e:
            logger.error(f"❌ Error checking channel: {e}")

    # Send welcome message
    try:
        caption = (
            f"Hi {message.from_user.mention()}! 👋\n\n"
            "🤖 **I'm a Telegram File to Link Generator Bot**\n"
            "📁 Send me any file and get direct download links!\n"
            "🎬 Supports streaming for videos and audio\n\n"
        )
        
        if hasattr(Var, 'DAILY_LIMIT_FILE') and not getattr(Var, 'PERIVEAT', True):
            caption += (
                f"📊 **Daily Limits:**\n"
                f"• Files: {Var.DAILY_LIMIT_FILE}\n"
                f"• Size: {byte_to_human_read(Var.DAILY_LIMIT_DOWNLOAD)}"
            )
            
        await message.reply_photo(
            photo="https://telegra.ph/file/ca10e459bc6f48a4ad0f7.jpg",
            caption=caption,
            reply_markup=buttonz
        )
        logger.info("✅ Welcome message sent")
        
    except Exception as e:
        logger.error(f"❌ Failed to send welcome: {e}")
        await message.reply_text("👋 Welcome! Send me any file to get download links.")


@StreamBot.on_message((filters.command("help") | filters.regex('Help📚')) & filters.private)
async def help_handler(client: Client, message: Message) -> None:
    """Handle /help command"""
    logger.info(f"❓ HELP: Command received from user {message.from_user.id}")
    
    try:
        help_text = (
            "📖 **How to use this bot:**\n\n"
            "1️⃣ Send me any file (video, audio, document, photo)\n"
            "2️⃣ Get instant download and streaming links\n"
            "3️⃣ Share links with anyone!\n\n"
            "🎯 **Commands:** /start, /help, /test\n"
            "💡 **Need help?** Contact the owner!"
        )
        
        await message.reply_text(
            help_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Contact Owner", url=f"tg://user?id={Var.OWNER_ID[0]}")]
            ])
        )
        logger.info("✅ Help message sent")
        
    except Exception as e:
        logger.error(f"❌ Failed to send help: {e}")


logger.info("🎯 start_help.py handlers registered successfully")