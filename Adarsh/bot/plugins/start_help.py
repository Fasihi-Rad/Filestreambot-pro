# (c) Fasihi-Rad
from pyrogram.types import ReplyKeyboardMarkup
from Adarsh.utils.file_properties import get_name, get_hash, get_media_file_size
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import filters
from Adarsh.utils.database import Database
from Adarsh.utils.human_readable import byte_to_human_read
from Adarsh.bot import StreamBot
from Adarsh.vars import Var
import logging
logger = logging.getLogger(__name__)
db = Database(Var.DATABASE_URL, Var.NAME)


buttonz = ReplyKeyboardMarkup(
    [
        ["Start⚡️", "Help📚", "Login🔑", "DC"],
        ["Support❤️", "Ping📡", "Status📊", "Maintainers😎"]

    ],
    resize_keyboard=True
)


@StreamBot.on_message((filters.command("start") | filters.regex('Start⚡️')) & filters.private)
async def start(b, m):
    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id, m.from_user.first_name, m.from_user.last_name, m.from_user.username)
        await b.send_message(
            Var.BIN_CHANNEL,
            f"**Nᴇᴡ Usᴇʀ Jᴏɪɴᴇᴅ:** \n\n__Mʏ Nᴇᴡ Fʀɪᴇɴᴅ__ [{m.from_user.first_name}](tg://user?id={m.from_user.id}) __Sᴛᴀʀᴛᴇᴅ Yᴏᴜʀ Bᴏᴛ !!__"
        )
    if Var.UPDATES_CHANNEL != "None":
        try:
            user = await b.get_chat_member(Var.UPDATES_CHANNEL, m.chat.id)
            if user.status == "kicked":
                await b.send_message(
                    chat_id=m.chat.id,
                    text="__𝓢𝓞𝓡𝓡𝓨, 𝓨𝓞𝓤 𝓐𝓡𝓔 𝓐𝓡𝓔 𝓑𝓐𝓝𝓝𝓔𝓓 𝓕𝓡𝓞𝓜 𝓤𝓢𝓘𝓝𝓖 𝓜𝓔. 𝓒ᴏɴᴛᴀᴄᴛ ᴛʜᴇ 𝓓ᴇᴠᴇʟᴏᴘᴇʀ__\n\n  **𝙃𝙚 𝙬𝙞𝙡𝙡 𝙝𝙚𝙡𝙥 𝙮𝙤𝙪**",
                    disable_web_page_preview=True
                )
                return
        except UserNotParticipant:
            await StreamBot.send_photo(
                chat_id=m.chat.id,
                photo="https://telegra.ph/file/9d94fc0af81234943e1a9.jpg",
                caption="<i>𝙹𝙾𝙸𝙽 CHANNEL 𝚃𝙾 𝚄𝚂𝙴 𝙼𝙴🔐</i>",
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
        except Exception:
            await b.send_message(
                chat_id=m.chat.id,
                text="<i>𝓢𝓸𝓶𝓮𝓽𝓱𝓲𝓷𝓰 𝔀𝓮𝓷𝓽 𝔀𝓻𝓸𝓷𝓰</i> <b> <a href='https://github.com/Fasihi-Rad'>CLICK HERE FOR SUPPORT </a></b>",

                disable_web_page_preview=True)
            return
    if not Var.PERIVEAT :
        await StreamBot.send_photo(
            chat_id=m.chat.id,
            photo="https://telegra.ph/file/ca10e459bc6f48a4ad0f7.jpg",
            caption=f'Hi {m.from_user.mention(style="md")}!,\nI am Telegram File to Link Generator Bot with Channel support.\n'\
                    f'Send me any file and get a direct download link and streamable link.!\n\n <b>If you are not Subscribed, You could download {Var.DAILY_LIMIT_FILE} files total {byte_to_human_read(Var.DAILY_LIMIT_DOWNLOAD)} size.</b>',
            reply_markup=buttonz)
    else:
        await StreamBot.send_photo(
            chat_id=m.chat.id,
            photo="https://telegra.ph/file/ca10e459bc6f48a4ad0f7.jpg",
            caption=f'Hi {m.from_user.mention(style="md")}!,\nI am Telegram File to Link Generator Bot with Channel support.\n'\
                    f'Send me any file and get a direct download link and streamable link.!\n',
            reply_markup=buttonz)


@StreamBot.on_message((filters.command("help") | filters.regex('Help📚')) & filters.private)
async def help_handler(bot, message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name, message.from_user.username)
        await bot.send_message(
            Var.BIN_CHANNEL,
            f"**Nᴇᴡ Usᴇʀ Jᴏɪɴᴇᴅ **\n\n__Mʏ Nᴇᴡ Fʀɪᴇɴᴅ__ [{message.from_user.first_name}](tg://user?id={message.from_user.id}) __Started Your Bot !!__"
        )
    if Var.UPDATES_CHANNEL != "None":
        try:
            user = await bot.get_chat_member(Var.UPDATES_CHANNEL, message.chat.id)
            if user.status == "kicked":
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f"<i>Sᴏʀʀʏ Sɪʀ, Yᴏᴜ ᴀʀᴇ Bᴀɴɴᴇᴅ FROM USING ᴍᴇ. Cᴏɴᴛᴀᴄᴛ the [Server Owner](tg://user?id={Var.OWNER_ID[0]})</i>",

                    disable_web_page_preview=True
                )
                return
        except UserNotParticipant:
            await StreamBot.send_photo(
                chat_id=message.chat.id,
                photo="https://telegra.ph/file/ca10e459bc6f48a4ad0f7.jpg",
                Caption="**𝙹𝙾𝙸𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃 𝙶𝚁𝙾𝚄𝙿 𝚃𝙾 𝚄𝚂𝙴 ᴛʜɪs Bᴏᴛ!**\n\n__Dᴜᴇ ᴛᴏ Oᴠᴇʀʟᴏᴀᴅ, Oɴʟʏ Cʜᴀɴɴᴇʟ Sᴜʙsᴄʀɪʙᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜᴇ Bᴏᴛ!__",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🤖 Jᴏɪɴ Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ", url=f"https://t.me/{Var.UPDATES_CHANNEL}")
                        ]
                    ]
                ),

            )
            return
        except Exception:
            await bot.send_message(
                chat_id=message.chat.id,
                text=f"__Sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ Wʀᴏɴɢ. Cᴏɴᴛᴀᴄᴛ the__ [Server Owner](tg://user?id={Var.OWNER_ID[0]}).",
                disable_web_page_preview=True)
            return
    if not Var.PERIVEAT :
        await message.reply_text(
            text=f"""<b>Send me any file or video I will give you streamable link and download link.</b>\n"""
                f"""<b>If you are not Subscribed, You could download {Var.DAILY_LIMIT_FILE} files total {byte_to_human_read(Var.DAILY_LIMIT_DOWNLOAD)} size.</b>"""
                """<b>I also support Channels, Add me to you Channel and send any media files and see miracle✨ Also send /list to know all commands.\nAdmins could use /admin to see admin's commands list.\n\n"""
                """<b>Don't Forget to use /support .😉</b>""",

            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("💁‍♂️ Server Owner", url=f"tg://user?id={Var.OWNER_ID[0]}")],
                    [InlineKeyboardButton("💥 Source Code", url="https://github.com/Fasihi-Rad/Filestreambot-pro/")]
                ]
            )
        )
    else:
        await message.reply_text(
            text=f"""<b>Send me any file or video I will give you streamable link and download link.</b>\n"""
                """<b>I also support Channels, Add me to you Channel and send any media files and see miracle✨ Also send /list to know all commands.\nAdmins could use /admin to see admin's commands list.\n\n"""
                """<b>Don't Forget to use /support .😉</b>""",

            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("💁‍♂️ Server Owner", url=f"tg://user?id={Var.OWNER_ID[0]}")],
                    [InlineKeyboardButton("💥 Source Code", url="https://github.com/Fasihi-Rad/Filestreambot-pro/")]
                ]
            )
        )
