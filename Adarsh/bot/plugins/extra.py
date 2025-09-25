# (c) Fasihi-Rad
import time
import shutil
import psutil
import logging
from typing import Optional

from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified, FloodWait

from Adarsh.bot import StreamBot
from Adarsh import StartTime
from Adarsh.vars import Var
from Adarsh.utils.database import Database
from Adarsh.utils.human_readable import byte_to_human_read

# Import utils_bot functions properly
try:
    from utils_bot import readable_time, get_readable_file_size
except ImportError:
    # Fallback implementations
    def readable_time(seconds: float) -> str:
        periods = [
            ('day', 60*60*24),
            ('hour', 60*60),
            ('minute', 60),
            ('second', 1)
        ]
        
        result = []
        for period_name, period_seconds in periods:
            if seconds > period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
                if int(period_value) > 0:
                    result.append(f"{int(period_value)} {period_name}{'s' if int(period_value) != 1 else ''}")
        
        return ', '.join(result) if result else "0 seconds"
    
    def get_readable_file_size(size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        size_name = ["B", "KB", "MB", "GB", "TB"]
        i = int((len(hex(size_bytes)) - 2) / 3.32193)
        if i >= len(size_name):
            i = len(size_name) - 1
        p = 1024 ** i
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

logger = logging.getLogger(__name__)
db = Database(Var.DATABASE_URL, Var.NAME)

START_TEXT = "🌐 **Your Telegram DC:** `{}`"


@StreamBot.on_message(filters.regex("Maintainers😎") | filters.command("maintainers"))
async def maintainers(client: Client, message: Message) -> None:
    """Show maintainers/developers information"""
    try:
        developer_info = (
            f"👨‍💻 **Developed by:** [Amir.r Fasihi.r](https://github.com/Fasihi-Rad)\n\n"
            f"🤖 **Bot maintained by:** [Server Owner](tg://user?id={Var.OWNER_ID[0]})\n\n"
            f"⭐ **Support the project:**\n"
            f"• Give a star to the repository\n"
            f"• Report bugs and suggest improvements\n"
            f"• Contribute to the codebase"
        )
        
        await message.reply_text(
            text=developer_info,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💻 Developer", url="https://github.com/Fasihi-Rad")],
                [InlineKeyboardButton("⭐ Source Code", url="https://github.com/Fasihi-Rad/Filestreambot-pro")]
            ]),
            disable_web_page_preview=True,
            quote=True
        )
        logger.info(f"User {message.from_user.id} accessed maintainers info")
        
    except Exception as e:
        logger.error(f"Error in maintainers command: {e}")
        await message.reply_text(
            "❌ An error occurred while fetching maintainer information.",
            quote=True
        )
            
@StreamBot.on_message(filters.regex("Support❤️") | filters.command("support"))
async def support_info(client: Client, message: Message) -> None:
    """Show support information"""
    try:
        support_text = (
            f"💝 **Support the Bot**\n\n"
            f"👨‍💻 **Server Owner:** [Contact Here](tg://user?id={Var.OWNER_ID[0]})\n\n"
            f"🎯 **How to support:**\n"
            f"• Report bugs and issues\n"
            f"• Share with friends\n"
            f"• Give feedback for improvements\n"
            f"• Contribute to development\n\n"
            f"💸 **Donate to keep server running:**\n"
            f"• Help cover server costs\n"
            f"• Enable new features development\n"
            f"• Maintain high-quality service"
        )
        
        support_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Contact Owner", url=f"tg://user?id={Var.OWNER_ID[0]}")],
            [InlineKeyboardButton("⭐ GitHub Repository", url="https://github.com/Fasihi-Rad/Filestreambot-pro")]
        ])
        
        await message.reply_text(
            text=support_text,
            reply_markup=support_markup,
            disable_web_page_preview=True,
            quote=True
        )
        logger.info(f"User {message.from_user.id} accessed support info")
        
    except Exception as e:
        logger.error(f"Error in support command: {e}")
        await message.reply_text(
            "❌ An error occurred while fetching support information.",
            quote=True
        )
@StreamBot.on_message(filters.regex("DC") | filters.command("dc"))
async def show_dc(client: Client, message: Message) -> None:
    """Show user's Telegram data center"""
    try:
        if not message.from_user:
            await message.reply_text("❌ Unable to determine your DC.", quote=True)
            return
            
        dc_id = message.from_user.dc_id
        if dc_id:
            dc_info = {
                1: "🇺🇸 Miami, USA",
                2: "🇳🇱 Amsterdam, Netherlands", 
                3: "🇺🇸 Miami, USA",
                4: "🇳🇱 Amsterdam, Netherlands",
                5: "🇸🇬 Singapore"
            }
            
            location = dc_info.get(dc_id, "Unknown Location")
            text = f"🌐 **Your Telegram Data Center:**\n\n📍 **DC {dc_id}:** {location}"
        else:
            text = "❌ Unable to determine your data center."
            
        await message.reply_text(
            text=text,
            disable_web_page_preview=True,
            quote=True
        )
        logger.info(f"User {message.from_user.id} checked their DC: {dc_id}")
        
    except Exception as e:
        logger.error(f"Error in DC command: {e}")
        await message.reply_text(
            "❌ An error occurred while checking your data center.",
            quote=True
        )

@StreamBot.on_message(filters.command("list"))
async def list_commands(client: Client, message: Message) -> None:
    """Show all available commands"""
    try:
        commands_list = (
            f"👋 Hi {message.from_user.mention(style='md')}!\n\n"
            f"📋 **Available Commands:**\n\n"
            f"🏠 **Basic Commands:**\n"
            f"• `Start⚡️` - Start the bot\n"
            f"• `Help📚` - Get help information\n"
            f"• `DC` - Show your Telegram data center\n\n"
            f"🔐 **Account Commands:**\n"
            f"• `Login🔑` - Login with password (if required)\n\n"
            f"📊 **Information Commands:**\n"
            f"• `Status📊` - Show bot/user statistics\n"
            f"• `Ping📡` - Check bot response time\n\n"
            f"❤️ **Support Commands:**\n"
            f"• `Support❤️` - Get support information\n"
            f"• `Maintainers😎` - View developer information\n\n"
            f"💡 **Tip:** Just send me any file to get download links!"
        )
        
        await message.reply_text(
            text=commands_list,
            quote=True
        )
        logger.info(f"User {message.from_user.id} requested commands list")
        
    except Exception as e:
        logger.error(f"Error in list command: {e}")
        await message.reply_text(
            "❌ An error occurred while fetching the commands list.",
            quote=True
        )
@StreamBot.on_message(filters.regex("Ping📡") | filters.command("ping"))
async def ping_bot(client: Client, message: Message) -> None:
    """Check bot response time"""
    try:
        # Check if user is banned
        user_status = await db.check_user_status(message.chat.id)
        if user_status == 'banned':
            await message.reply_text(
                "❌ You are banned from using this bot.\n"
                f"Contact [Server Owner](tg://user?id={Var.OWNER_ID[0]}) for assistance.",
                quote=True,
                disable_web_page_preview=True
            )
            return
            
        start_time = time.time()
        temp_msg = await message.reply_text("🏓 Pinging...", quote=True)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000
        
        ping_text = (
            f"🏓 **Pong!**\n\n"
            f"⚡ **Response Time:** `{response_time:.2f}ms`\n"
            f"🤖 **Bot Status:** Online ✅\n"
            f"📡 **Server:** Running smoothly"
        )
        
        await temp_msg.edit_text(ping_text)
        logger.info(f"User {message.from_user.id} pinged bot - {response_time:.2f}ms")
        
    except Exception as e:
        logger.error(f"Error in ping command: {e}")
        try:
            await message.reply_text("❌ An error occurred while pinging.", quote=True)
        except:
            pass
    
@StreamBot.on_message(filters.private & filters.regex("Status📊"))
async def show_status(client: Client, message: Message) -> None:
    """Show bot status and user statistics"""
    try:
        user_id = message.from_user.id
        
        # Check if user is admin
        if user_id in Var.OWNER_ID:
            await show_admin_stats(client, message)
        else:
            await show_user_stats(client, message)
            
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await message.reply_text("❌ An error occurred while fetching statistics.", quote=True)


async def show_admin_stats(client: Client, message: Message) -> None:
    """Show admin statistics including server stats"""
    try:
        # Calculate uptime
        current_time = readable_time(time.time() - StartTime)
        
        # Get disk usage
        total, used, free = shutil.disk_usage('.')
        total_size = get_readable_file_size(total)
        used_size = get_readable_file_size(used)
        free_size = get_readable_file_size(free)
        
        # Get network usage
        net_io = psutil.net_io_counters()
        sent = get_readable_file_size(net_io.bytes_sent)
        recv = get_readable_file_size(net_io.bytes_recv)
        
        # Get system stats
        cpu_usage = psutil.cpu_percent(interval=0.5)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        
        # Get database stats
        total_users = await db.total_users_count()
        
        admin_stats = (
            f"📊 **Bot Statistics (Admin)**\n\n"
            f"⏰ **Uptime:** `{current_time}`\n"
            f"👥 **Total Users:** `{total_users:,}`\n\n"
            f"💾 **Storage:**\n"
            f"• Total: `{total_size}`\n"
            f"• Used: `{used_size}`\n"
            f"• Free: `{free_size}`\n\n"
            f"🌐 **Network Usage:**\n"
            f"• Upload: `{sent}`\n"
            f"• Download: `{recv}`\n\n"
            f"⚡ **System Resources:**\n"
            f"• CPU: `{cpu_usage}%`\n"
            f"• RAM: `{memory_usage}%`\n"
            f"• Disk: `{disk_usage}%`"
        )
        
        await message.reply_text(admin_stats, quote=True)
        logger.info(f"Admin {message.from_user.id} checked bot statistics")
        
    except Exception as e:
        logger.error(f"Error showing admin stats: {e}")
        await message.reply_text("❌ Failed to fetch admin statistics.", quote=True)


async def show_user_stats(client: Client, message: Message) -> None:
    """Show user-specific statistics"""
    try:
        user_id = message.from_user.id
        
        # Update user limits (reset if new day)
        await db.update_user_link_limit(user_id)
        
        # Get user info
        user_info = await db.user_info(user_id)
        if not user_info:
            await message.reply_text("❌ User information not found.", quote=True)
            return
            
        # Calculate uptime
        current_time = readable_time(time.time() - StartTime)
        
        # Format user stats
        user_stats = (
            f"📊 **Your Statistics**\n\n"
            f"⏰ **Bot Uptime:** `{current_time}`\n\n"
            f"👤 **Your Account:**\n"
            f"• Status: `{user_info.get('status', 'Unknown')}`\n"
            f"• Member Since: `{user_info.get('join_date', 'Unknown')}`\n\n"
            f"📈 **Today's Usage:**\n"
            f"• Links Created: `{user_info.get('link_made', 0)}`\n"
            f"• Data Downloaded: `{byte_to_human_read(user_info.get('total_download', 0))}`\n\n"
        )
        
        # Add limits info for free users
        if user_info.get('status') == 'free':
            user_stats += (
                f"⚠️ **Daily Limits:**\n"
                f"• Max Files: `{Var.DAILY_LIMIT_FILE}`\n"
                f"• Max Size: `{byte_to_human_read(Var.DAILY_LIMIT_DOWNLOAD)}`\n\n"
                f"💡 Contact admin for premium access!"
            )
        
        await message.reply_text(user_stats, quote=True)
        logger.info(f"User {user_id} checked their statistics")
        
    except Exception as e:
        logger.error(f"Error showing user stats for {message.from_user.id}: {e}")
        await message.reply_text("❌ Failed to fetch your statistics.", quote=True)