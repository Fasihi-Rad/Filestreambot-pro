# (c) Fasihi-Rad
import logging
from typing import Optional
from pyrogram import filters, Client
from pyrogram.types import Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, PeerIdInvalid, ChannelInvalid
from pyrogram.enums import ChatMemberStatus

from Adarsh.bot import StreamBot
from Adarsh.utils.database import Database
from Adarsh.utils.human_readable import byte_to_human_read
from Adarsh.vars import Var

logger = logging.getLogger(__name__)
db = Database(Var.DATABASE_URL, Var.NAME)

# Add startup logging to verify plugin loading
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
    try:
        logger.info(f"🎯 START: Start command received from user {message.from_user.id} (@{message.from_user.username})")
        
        # Test basic response first
        try:
            await message.reply_text("🤖 Bot is responding! Checking database connection...")
            logger.info("✅ START: Basic response sent successfully")
        except Exception as e:
            logger.error(f"❌ START: Failed to send basic response: {e}")
            return
        
        if not await db.is_user_exist(message.from_user.id):
            logger.info(f"👤 START: Adding new user: {message.from_user.id}")
            await db.add_user(
                message.from_user.id, 
                message.from_user.first_name, 
                message.from_user.last_name, 
                message.from_user.username
            )
            
            try:
                await client.send_message(
                    Var.BIN_CHANNEL,
                    f"**Nᴇᴡ Usᴇʀ Jᴏɪɴᴇᴅ:** \n\n"
                    f"__Mʏ Nᴇᴡ Fʀɪᴇɴᴅ__ [{message.from_user.first_name}]"
                    f"(tg://user?id={message.from_user.id}) __Sᴛᴀʀᴛᴇᴅ Yᴏᴜʀ Bᴏᴛ !!__"
                )
                logger.info(f"📢 START: Sent new user notification to channel {Var.BIN_CHANNEL}")
            except Exception as e:
                logger.error(f"❌ START: Failed to send new user notification: {e}")
        else:
            logger.info(f"👤 START: Existing user: {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ START: Failed to add new user {message.from_user.id}: {e}")
        try:
            await message.reply_text("❌ Database error occurred. Check logs.")
        except:
            logger.error("❌ START: Could not even send error message")

# Register the handler startup log
logger.info("🎯 START handler registered successfully")
    # Check channel subscription if required
    if Var.UPDATES_CHANNEL != "None":
        try:
            member = await client.get_chat_member(Var.UPDATES_CHANNEL, message.chat.id)
            if member.status == ChatMemberStatus.BANNED:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="__𝓢𝓞𝓡𝓡𝓨, 𝓨𝓞𝓤 𝓐𝓡𝓔 𝓐𝓝𝓝𝓔𝓓 𝓕𝓡𝓞𝓜 𝓤𝓢𝓘𝓝𝓖 𝓜𝓔.__\n\n"
                         f"**Contact [Server Owner](tg://user?id={Var.OWNER_ID[0]}) for help**",
                    disable_web_page_preview=True
                )
                return
                
        except UserNotParticipant:
            await client.send_photo(
                chat_id=message.chat.id,
                photo="https://telegra.ph/file/9d94fc0af81234943e1a9.jpg",
                caption="<i>𝙹𝙾𝙸𝙽 CHANNEL 𝚃𝙾 𝚄𝚂𝙴 𝙼𝙴🔐</i>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "Jᴏɪɴ ɴᴏᴡ 🔓", 
                        url=f"https://t.me/{Var.UPDATES_CHANNEL}"
                    )]
                ])
            )
            return
            
        except (PeerIdInvalid, ChannelInvalid) as e:
            logger.error(f"Invalid channel configuration: {e}")
            await client.send_message(
                chat_id=message.chat.id,
                text="<i>Channel configuration error. Contact support.</i>",
                disable_web_page_preview=True
            )
            return
            
        except Exception as e:
            logger.error(f"Error checking channel membership: {e}")
            await client.send_message(
                chat_id=message.chat.id,
                text="<i>𝓢𝓸𝓶𝓮𝓽𝓱𝓲𝓷𝓰 𝔀𝓮𝓷𝓽 𝔀𝓻𝓸𝓷𝓰</i> "
                     "<b><a href='https://github.com/Fasihi-Rad'>CLICK HERE FOR SUPPORT</a></b>",
                disable_web_page_preview=True
            )
            return
    # Send welcome message based on configuration
    try:
        welcome_photo = "https://telegra.ph/file/ca10e459bc6f48a4ad0f7.jpg"
        base_caption = (
            f'Hi {message.from_user.mention(style="md")}!,\n'
            'I am Telegram File to Link Generator Bot with Channel support.\n'
            'Send me any file and get a direct download link and streamable link!'
        )
        
        if not Var.PERIVEAT:
            # Free version with limits
            caption = (
                f'{base_caption}\n\n'
                f'<b>Daily Limits for free users:</b>\n'
                f'• Files: {Var.DAILY_LIMIT_FILE}\n'
                f'• Total size: {byte_to_human_read(Var.DAILY_LIMIT_DOWNLOAD)}'
            )
        else:
            # Private version without showing limits
            caption = base_caption
            
        await client.send_photo(
            chat_id=message.chat.id,
            photo=welcome_photo,
            caption=caption,
            reply_markup=buttonz
        )
        
    except Exception as e:
        logger.error(f"Failed to send welcome message: {e}")
        await message.reply_text("Welcome! Send me any file to get a download link.")


@StreamBot.on_message((filters.command("help") | filters.regex('Help📚')) & filters.private)
async def help_handler(client: Client, message: Message) -> None:
    """Handle /help command and Help button"""
    try:
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(
                message.from_user.id, 
                message.from_user.first_name, 
                message.from_user.last_name, 
                message.from_user.username
            )
            
            try:
                await client.send_message(
                    Var.BIN_CHANNEL,
                    f"**Nᴇᴡ Usᴇʀ Jᴏɪɴᴇᴅ**\n\n"
                    f"__Mʏ Nᴇᴡ Fʀɪᴇɴᴅ__ [{message.from_user.first_name}]"
                    f"(tg://user?id={message.from_user.id}) __Started Your Bot !!__"
                )
            except Exception as e:
                logger.error(f"Failed to send new user notification: {e}")
    except Exception as e:
        logger.error(f"Failed to add new user {message.from_user.id}: {e}")
    # Check channel subscription if required  
    if Var.UPDATES_CHANNEL != "None":
        try:
            member = await client.get_chat_member(Var.UPDATES_CHANNEL, message.chat.id)
            if member.status == ChatMemberStatus.BANNED:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"<i>Sᴏʀʀʏ Sɪʀ, Yᴏᴜ ᴀʀᴇ Bᴀɴɴᴇᴅ FROM USING ᴍᴇ.</i>\n\n"
                         f"**Contact [Server Owner](tg://user?id={Var.OWNER_ID[0]}) for help**",
                    disable_web_page_preview=True
                )
                return
                
        except UserNotParticipant:
            await client.send_photo(
                chat_id=message.chat.id,
                photo="https://telegra.ph/file/ca10e459bc6f48a4ad0f7.jpg",
                caption="**𝙹𝙾𝙸𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃 𝙶𝚁𝙾𝚄𝙿 𝚃𝙾 𝚄𝚂𝙴 ᴛʜɪs Bᴏᴛ!**\n\n"
                        "__Dᴜᴇ ᴛᴏ Oᴠᴇʀʟᴏᴀᴅ, Oɴʟʏ Cʜᴀɴɴᴇʟ Sᴜʙsᴄʀɪʙᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜᴇ Bᴏᴛ!__",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "🤖 Jᴏɪɴ Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ", 
                        url=f"https://t.me/{Var.UPDATES_CHANNEL}"
                    )]
                ])
            )
            return
            
        except Exception as e:
            logger.error(f"Error checking channel membership in help: {e}")
            await client.send_message(
                chat_id=message.chat.id,
                text=f"__Sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ Wʀᴏɴɢ.__\n\n"
                     f"**Contact [Server Owner](tg://user?id={Var.OWNER_ID[0]}) for support**",
                disable_web_page_preview=True
            )
            return
    # Send help message
    try:
        base_help = (
            "<b>📝 How to use this bot:</b>\n\n"
            "• Send me any file or video and I will give you streamable and download links\n"
            "• I also support Channels - Add me to your channel and send media files\n"
            "• Use /list to see all available commands\n"
            "• Admins can use /admin to see admin commands\n\n"
            "<b>Don't forget to use /support for help! 😉</b>"
        )
        
        help_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💁‍♂️ Server Owner", url=f"tg://user?id={Var.OWNER_ID[0]}")],
            [InlineKeyboardButton("💥 Source Code", url="https://github.com/Fasihi-Rad/Filestreambot-pro/")]
        ])
        
        if not Var.PERIVEAT:
            # Free version - show limits
            help_text = (
                f"{base_help}\n\n"
                f"<b>📊 Daily Limits for free users:</b>\n"
                f"• Files: {Var.DAILY_LIMIT_FILE}\n"
                f"• Total size: {byte_to_human_read(Var.DAILY_LIMIT_DOWNLOAD)}"
            )
        else:
            # Private version - no limits shown
            help_text = base_help
            
        await message.reply_text(
            text=help_text,
            disable_web_page_preview=True,
            reply_markup=help_markup
        )
        
    except Exception as e:
        logger.error(f"Failed to send help message: {e}")
        await message.reply_text(
            "Send me any file and I'll generate download links for you!\n"
            "Use /list for more commands."
        )
