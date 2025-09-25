# (c) Fasihi-Rad
from pyrogram import Client, enums
import pyromod.listen
from ..config import config
import logging
import os

# Create session directory if it doesn't exist
os.makedirs("./session", exist_ok=True)

# Configure logging for pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pyrogram.session.session").setLevel(logging.WARNING)
logging.getLogger("pyrogram.connection.connection").setLevel(logging.WARNING)

# Main bot client with modern configuration
StreamBot = Client(
    name='FileStreamBot',
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token,
    sleep_threshold=config.sleep_threshold,
    workers=config.workers,
    workdir="./session",
    plugins=dict(root="Adarsh.bot.plugins"),
    parse_mode=enums.ParseMode.HTML,  # Modern enum usage
    max_concurrent_transmissions=config.max_concurrent_transmissions,
)

# Multi-client support
multi_clients = {}
work_loads = {}

# Set default parse mode for backward compatibility
StreamBot.parse_mode = enums.ParseMode.HTML