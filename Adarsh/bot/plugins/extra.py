from Adarsh.bot import StreamBot
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import filters
import time
import shutil, psutil
from utils_bot import *
from Adarsh import StartTime
from Adarsh.vars import Var
from Adarsh.utils.database import Database

db = Database(Var.DATABASE_URL, Var.NAME)

START_TEXT = """ Your Telegram DC Is : `{}`  """



@StreamBot.on_message(filters.regex("Maintainers😎"))
async def maintainers(b,m):
    try:
       await b.send_message(chat_id=m.chat.id,text="HELLO",quote=True)
    except Exception:
                await b.send_message(
                    chat_id=m.chat.id,
                    text=f"<b>Coded By [Adarsh Goel](https://github.com/adarsh-goel)\nModified By [Server Owner](tg://user?id={Var.OWNER_ID[0]})</b>",
                    
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("Developer💻", url=f"https://github.com/adarsh-goel")
                            ]
                        ]
                    ),
                    
                    disable_web_page_preview=True)
            
         
@StreamBot.on_message(filters.regex("Support❤️"))
async def follow_user(b,m):
    try:
       await b.send_message(chat_id=m.chat.id,text="HELLO",quote=True)
    except Exception:
                await b.send_message(
                        chat_id=m.chat.id,
                        text=f"<b>Support [Server Owner](tg://user?id={Var.OWNER_ID[0]}) By Donation</b>\n"\
                             f"Please, Support me For keep the server runing \n"\
                             f"Donation by Crypto :",
                    
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("Donate", url=f"")
                            ]
                        ]
                    ),
                    
                    disable_web_page_preview=True)
        

@StreamBot.on_message(filters.regex("DC"))
async def start(bot, update):
    text = START_TEXT.format(update.from_user.dc_id)
    await update.reply_text(
        text=text,
        disable_web_page_preview=True,
        quote=True
    )

    
    
@StreamBot.on_message(filters.command("list"))
async def list(l, m):
    LIST_MSG = "Hi! {} Here is a list of all my commands \n \n 1 . `Start⚡️` \n 2. `Help📚` \n 3. `Login🔑` \n 4. `Support❤️` \n 5. `Ping📡` \n 6. `Status📊` \n 7. `DC` This tells your telegram data center \n 8. `Maintainers😎` "
    await l.send_message(chat_id = m.chat.id,
        text = LIST_MSG.format(m.from_user.mention(style="md"))
        
    )
    
    
@StreamBot.on_message(filters.regex("Ping📡"))
async def ping(b, m):
    if await db.check_user_status(m.chat.id) != 'ban':
        start_t = time.time()
        ag = await m.reply_text("....")
        end_t = time.time()
        time_taken_s = (end_t - start_t) * 1000
        await ag.edit(f"Pong!\n{time_taken_s:.3f} ms")
    
    
    
@StreamBot.on_message(filters.private & filters.regex("Status📊"))
async def stats(bot, update):
    user_id=update.from_user.id
    if user_id in Var.OWNER_ID:
        currentTime = readable_time((time.time() - StartTime))
        total, used, free = shutil.disk_usage('.')
        total = get_readable_file_size(total)
        used = get_readable_file_size(used)
        free = get_readable_file_size(free)
        sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
        recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
        cpuUsage = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        botstats = f'<b>Bot Uptime:</b> {currentTime}\n' \
                f'<b>Total disk space:</b> {total}\n' \
                f'<b>Used:</b> {used}  ' \
                f'<b>Free:</b> {free}\n\n' \
                f'📊Data Usage📊\n<b>Upload:</b> {sent}\n' \
                f'<b>Down:</b> {recv}\n\n' \
                f'<b>CPU:</b> {cpuUsage}% ' \
                f'<b>RAM:</b> {memory}% ' \
                f'<b>Disk:</b> {disk}%'
        await update.reply_text(botstats)
    else:
        await update.reply_text(f"<b>You don't have the permission !</b>")