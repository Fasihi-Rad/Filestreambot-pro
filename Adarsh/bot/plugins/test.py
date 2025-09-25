# Simple test plugin to verify bot functionality
import logging
from pyrogram import filters
from pyrogram.types import Message
from Adarsh.bot import StreamBot

logger = logging.getLogger(__name__)
logger.info("🧪 test.py plugin loaded successfully")

@StreamBot.on_message(filters.command(["test", "ping"]) & filters.private)
async def test_command(client, message: Message):
    """Simple test command to verify bot is receiving messages"""
    logger.info(f"🧪 TEST: Received test command from user {message.from_user.id} (@{message.from_user.username})")
    try:
        await message.reply_text(
            f"✅ **Bot is working!**\n\n"
            f"🤖 Bot: @{client.me.username}\n"
            f"👤 User: {message.from_user.first_name}\n"
            f"🆔 User ID: `{message.from_user.id}`\n"
            f"📝 Command: `{message.text}`\n\n"
            f"🔌 Plugins are loading correctly!"
        )
        logger.info("🧪 TEST: Response sent successfully")
    except Exception as e:
        logger.error(f"🧪 TEST: Failed to send response: {e}")

@StreamBot.on_message(filters.command("start") & filters.private)
async def simple_start_command(client, message: Message):
    """Simple start command as fallback"""
    logger.info(f"� SIMPLE START: Received from user {message.from_user.id} (@{message.from_user.username})")
    try:
        await message.reply_text(
            f"👋 **Hello {message.from_user.first_name}!**\n\n"
            f"🤖 I'm a File to Link bot\n"
            f"📁 Send me any file and I'll generate download links\n\n"
            f"🧪 Use /test to verify I'm working properly"
        )
        logger.info("🚀 SIMPLE START: Response sent successfully")
    except Exception as e:
        logger.error(f"🚀 SIMPLE START: Failed to send response: {e}")

logger.info("🧪 Test handlers registered successfully")