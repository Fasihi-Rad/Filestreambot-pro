# (c) Fasihi-Rad
import os
import asyncio
from asyncio import TimeoutError
from Adarsh.bot import StreamBot
from Adarsh.utils.database import Database
from Adarsh.utils.human_readable import byte_to_human_read
from Adarsh.vars import Var
from urllib.parse import quote_plus
from pyrogram import filters, Client
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from Adarsh.utils.file_properties import get_name, get_hash, get_media_file_size
from os import getenv
db = Database(Var.DATABASE_URL, Var.NAME)


@StreamBot.on_message((filters.regex("Login🔑") | filters.command("login")), group=4)
async def login_handler(c: Client, m: Message):
    try:
        try:
            ag = await m.reply_text("<b>Now send me password.</b>\n\n __You can use /cancel command to cancel the process__")
            _text = await c.listen(m.chat.id, filters=filters.text, timeout=90)
            if _text.text:
                textp = _text.text
                if textp == "/cancel":
                    await m.reply_text("Process Cancelled")
                    return
            else:
                return
        except TimeoutError:
            await ag.edit("I can't wait more for password, try again")
            return
        if textp == Var.SUB_PASS:
            await db.login_user(m.chat.id, m.chat.first_name, m.chat.last_name, m.chat.username)
            await m.reply_text("Password is correct")
        else:
            await m.reply_text("Wrong password, Try again")
    except Exception as e:
        print(e)


@StreamBot.on_message((filters.private) & (filters.document | filters.video | filters.audio | filters.photo), group=4)
async def private_receive_handler(c: Client, m: Message):
    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id, m.from_user.first_name, m.from_user.last_name, m.from_user.username)
        await c.send_message(
            Var.BIN_CHANNEL,
            f"New User Joined! : \n\n Name : [{m.from_user.first_name}](tg://user?id={m.from_user.id}) Started Your Bot!!"
        )

    if Var.PERIVEAT:
        if await db.check_user_status(m.chat.id) == 'free':
            await m.reply_text(f"<b>Login first using /login cmd</b> \nDon't know the pass? request it from the [Server Owner](tg://user?id={Var.OWNER_ID[0]})")
            return

    if await db.check_user_status(m.chat.id) == 'banned':
        await c.send_message(
            chat_id=m.chat.id,
            text=f"You are banned!\n\n  **Cᴏɴᴛᴀᴄᴛ [Server Owner](tg://user?id={Var.OWNER_ID[0]}) ʜᴇ Wɪʟʟ Hᴇʟᴘ Yᴏᴜ**",
            disable_web_page_preview=True
        )
        return

    if not Var.PERIVEAT:
        valid = await db.check_user_link_limit(m.chat.id, get_media_file_size(m))
        if valid == False:
            await c.send_message(
                chat_id=m.chat.id,
                text=f"Your daily limit is over \nTry Tomorrow!\nUse `/help` for more info\n",
                disable_web_page_preview=True
            )
            return
        elif valid == 2:
            await c.send_message(
                chat_id=m.chat.id,
                text=f"It's Too big, it's should be under {byte_to_human_read(Var.DAILY_LIMIT_DOWNLOAD)} .\nUse `/help` for more info.",
                disable_web_page_preview=True
            )
            return

    if Var.UPDATES_CHANNEL != "None":
        try:
            user = await c.get_chat_member(Var.UPDATES_CHANNEL, m.chat.id)
            if user.status == "kicked":
                await c.send_message(
                    chat_id=m.chat.id,
                    text=f"You are banned!\n\n  **Cᴏɴᴛᴀᴄᴛ [Server Owner](tg://user?id={Var.OWNER_ID[0]}) ʜᴇ Wɪʟʟ Hᴇʟᴘ Yᴏᴜ**",
                    disable_web_page_preview=True
                )
                return

        except UserNotParticipant:
            await c.send_message(
                chat_id=m.chat.id,
                text="""<i>𝙹𝙾𝙸𝙽 UPDATES CHANNEL 𝚃𝙾 𝚄𝚂𝙴 𝙼𝙴 🔐</i>""",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Jᴏɪɴ ɴᴏᴡ 🔓", url=f"https://t.me/{Var.UPDATES_CHANNEL}")
                        ]
                    ]
                ),

            )
            return

        except Exception as e:
            await m.reply_text(e)
            await c.send_message(
                chat_id=m.chat.id,
                text=f"**Sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ Wʀᴏɴɢ. Cᴏɴᴛᴀᴄᴛ ᴍʏ ʙᴏss** [Server Owner](tg://user?id={Var.OWNER_ID[0]})",

                disable_web_page_preview=True)
            return
    try:
        log_msg = await m.forward(chat_id=Var.BIN_CHANNEL)
        stream_link = "http://{}:{}/watch/{}/{}?hash={}".format(
            Var.FQDN, Var.PORT, log_msg.id, quote_plus(get_name(log_msg)), get_hash(log_msg))
        online_link = "http://{}:{}/{}/{}?hash={}".format(
            Var.FQDN, Var.PORT, log_msg.id, quote_plus(get_name(log_msg)), get_hash(log_msg))

        msg_text = """<i><u>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 !</u></i>\n\n<b>📂 Fɪʟᴇ ɴᴀᴍᴇ :</b> <i>{}</i>\n\n<b>📦 Fɪʟᴇ ꜱɪᴢᴇ :</b> <i>{}</i>\n\n<b>📥 Dᴏᴡɴʟᴏᴀᴅ :</b> <i>{}</i>\n\n<b> 🖥WATCH  :</b> <i>{}</i>\n\n<b>🚸 Nᴏᴛᴇ : LINK WON'T EXPIRE TILL I DELETE</b>"""
        
        await db.add_download_size(m.chat.id, get_media_file_size(m))
        await db.increase_link(m.chat.id)
        
        await log_msg.reply_text(text=f"**RᴇQᴜᴇꜱᴛᴇᴅ ʙʏ :** [{m.from_user.first_name} {m.from_user.last_name}](tg://user?id={m.from_user.id})\n**Uꜱᴇʀ ɪᴅ :** `{m.from_user.id}`\n**Stream ʟɪɴᴋ :** {stream_link}", disable_web_page_preview=True,  quote=True)
        await m.reply_text(
            text=msg_text.format(get_name(log_msg), byte_to_human_read(get_media_file_size(m)), online_link, stream_link),
            quote=True,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("STREAM 🖥", url=stream_link),  # Stream Link
                                                InlineKeyboardButton('DOWNLOAD 📥', url=online_link)]])  # Download Link
        )

    except FloodWait as e:
        print(f"Sleeping for {str(e.x)}s")
        await asyncio.sleep(e.x)
        await c.send_message(chat_id=Var.BIN_CHANNEL, text=f"Gᴏᴛ FʟᴏᴏᴅWᴀɪᴛ ᴏғ {str(e.x)}s from [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n\n**𝚄𝚜𝚎𝚛 𝙸𝙳 :** `{str(m.from_user.id)}`", disable_web_page_preview=True)


@StreamBot.on_message(filters.channel & ~filters.group & (filters.document | filters.video | filters.photo) & ~filters.forwarded, group=-1)
async def channel_receive_handler(bot, broadcast):
    
    if Var.PERIVEAT:
        if await db.check_user_status(broadcast.chat.id) == 'free':
            await broadcast.reply_text("<b>Login first using /login cmd</b> \n Don't know the pass? request it from the Developer")
            return

    if int(broadcast.chat.id) in Var.BANNED_CHANNELS:
        await bot.leave_chat(broadcast.chat.id)
        return

    if not Var.PERIVEAT:
        valid = await db.check_user_link_limit(broadcast.chat.id, get_media_file_size(broadcast))
        if  valid == False:
            await broadcast.send_message(
                chat_id=broadcast.chat.id,
                text=f"Your daily limit is over \nTry Tomorrow!\nUse `/help` for more info\n",
                disable_web_page_preview=True
            )
            return
        elif valid == 2:
            await broadcast.send_message(
                chat_id=broadcast.chat.id,
                text=f"It's Too big, it's should be under {byte_to_human_read(Var.DAILY_LIMIT_DOWNLOAD)} .\nUse `/help` for more info.",
                disable_web_page_preview=True
            )
            return

    try:
        log_msg = await broadcast.forward(chat_id=Var.BIN_CHANNEL)
        stream_link = "http://{}:{}/watch/{}/{}?hash={}".format(
            Var.FQDN, Var.PORT, log_msg.id, quote_plus(get_name(log_msg)), get_hash(log_msg))
        online_link = "http://{}:{}/{}/{}?hash={}".format(
            Var.FQDN, Var.PORT, log_msg.id, quote_plus(get_name(log_msg)), get_hash(log_msg))
        await log_msg.reply_text(
            text=f"**Channel Name:** `{broadcast.chat.title}`\n**CHANNEL ID:** `{broadcast.chat.id}`\n**Rᴇǫᴜᴇsᴛ ᴜʀʟ:** {stream_link}",
            quote=True
        )
        await bot.edit_message_reply_markup(
            chat_id=broadcast.chat.id,
            message_id=broadcast.id,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🖥STREAM ", url=stream_link),
                     InlineKeyboardButton('Dᴏᴡɴʟᴏᴀᴅ📥', url=online_link)]
                ]
            )
        )
    except FloodWait as w:
        print(f"Sleeping for {str(w.x)}s")
        await asyncio.sleep(w.x)
        await bot.send_message(chat_id=Var.BIN_CHANNEL,
                               text=f"GOT FLOODWAIT OF {str(w.x)}s FROM {broadcast.chat.title}\n\n**CHANNEL ID:** `{str(broadcast.chat.id)}`",
                               disable_web_page_preview=True)
    except Exception as e:
        await bot.send_message(chat_id=Var.BIN_CHANNEL, text=f"**#ERROR_TRACKEBACK:** `{e}`", disable_web_page_preview=True)
        print(
            f"Cᴀɴ'ᴛ Eᴅɪᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ!\nEʀʀᴏʀ:  **Give me edit permission in updates and bin Channel!{e}**")
