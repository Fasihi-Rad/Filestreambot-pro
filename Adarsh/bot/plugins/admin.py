# (c) @adarsh-goel
import os
import time
import string
import random
import asyncio
import aiofiles
import datetime
import re
from Adarsh.utils.broadcast_helper import send_msg
from Adarsh.utils.database import Database
from Adarsh.bot import StreamBot
from Adarsh.vars import Var
from pyrogram import filters, Client
from pyrogram.types import Message

db = Database(Var.DATABASE_URL, Var.NAME)
Broadcast_IDs = {}

@StreamBot.on_message(filters.command("admin") & filters.private )
async def sts(c: Client, m: Message):
    user_id=m.from_user.id
    if user_id in Var.OWNER_ID:
        LIST_MSG = "Hi ! {} Here is a list of all Admin commands \n \n 1 . `/Admin` \n 2. `/users` : Display The Number of Users \n 3. `/userslist` : Display The Names of All Users \n 4. `/deluser` __ID__ : Delete The User \n 5. `/banuser` __ID__ : Ban The User \n 6. `/Status📊` \n 7. `/userinfo` __ID__ : Display The User Info \n 8. `/broadcast` "
        await c.send_message(chat_id = m.chat.id,
            text = LIST_MSG.format(m.from_user.mention(style="md"))
        )

@StreamBot.on_message(filters.command("users") & filters.private )
async def sts(c: Client, m: Message):
    user_id=m.from_user.id
    if user_id in Var.OWNER_ID:
        total_users = await db.total_users_count()
        await m.reply_text(text=f"<b>Total Users in DB: {total_users}</b>", quote=True)

@StreamBot.on_message(filters.command("userslist") & filters.private )       
async def sts(c: Client, m: Message):
    user_id=m.from_user.id
    if user_id in Var.OWNER_ID:
        await m.reply_text(text=f"<b>It's may take several moment !</b> \n__Please Wait__ ", quote=True)
        users_list = []
        all_users = await db.get_all_users()
        async for user in all_users:
            users_list.append(f"[{user['name']}](tg://user?id={user['id']})")
        await m.reply_text(text="All Users: \n\n" + ('   '.join(users_list)), quote=True)
        
@StreamBot.on_message(filters.command("deluser") & filters.private )       
async def sts(c: Client, m: Message):
    user_id=m.from_user.id
    if user_id in Var.OWNER_ID:
        deluser_ids = re.findall(r"([\d]+)", m.text)
        await m.reply_text(text=f"<b>It's may take several moment !</b> \n Users : {deluser_ids} ", quote=True)
        for deluser_id in deluser_ids:
            await db.delete_user(deluser_id)
            await m.reply_text(text=f"<b>User [{deluser_id}](tg://user?id={deluser_id}) deleted.</b>", quote=True)

@StreamBot.on_message(filters.command("banuser") & filters.private )       
async def sts(c: Client, m: Message):
    user_id=m.from_user.id
    if user_id in Var.OWNER_ID:
        banuser_ids = re.findall(r"([\d]+)", m.text)
        await m.reply_text(text=f"<b>It's may take several moment !</b> \n Users : {banuser_ids} ", quote=True)
        for banuser_id in banuser_ids:
            await db.ban_user(banuser_id)
            await m.reply_text(text=f"<b>User [{banuser_id}](tg://user?id={banuser_ids}) baned.</b>", quote=True)

@StreamBot.on_message(filters.command("userinfo") & filters.private )       
async def sts(c: Client, m: Message):
    user_id=m.from_user.id
    if user_id in Var.OWNER_ID:
        userinfo_ids = re.findall(r"([\d]+)", m.text)
        await m.reply_text(text=f"<b>It's may take several moment !</b>", quote=True)
        for userinfo_id in userinfo_ids:
            user = await db.user_info(userinfo_id)
            botstats = f'<b>User [{user["name"]}](tg://user?id={userinfo_ids}) Info : </b> \n\n' \
                f'<b>Telegram ID:` {user["id"]}`</b>\n' \
                f'<b>Name:</b> `{user["name"]}`\n' \
                f'<b>Telegram Username:</b> `{user["telegram_username"]}`\n' \
                f'<b>Status:</b> `{user["status"]}`\n' \
                f'<b>Links Made:</b> `{user["link_made"]}`\n' \
                f'<b>Join Date:</b> `{user["join_date"]}`\n'
            await m.reply_text(botstats)
        
@StreamBot.on_message(filters.command("broadcast") & filters.private  & filters.user(list(Var.OWNER_ID)))
async def broadcast_(c, m: Message):
    user_id=m.from_user.id
    out = await m.reply_text(
            text=f"Broadcast initiated! You will be notified with log file when all the users are notified."
    )
    all_users = await db.get_all_users()
    broadcast_msg = m.reply_to_message
    while True:
        broadcast_id = ''.join([random.choice(string.ascii_letters) for i in range(3)])
        if not Broadcast_IDs.get(broadcast_id):
            break
    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    failed = 0
    success = 0
    Broadcast_IDs[broadcast_id] = dict(
        total=total_users,
        current=done,
        failed=failed,
        success=success
    )
    async with aiofiles.open('broadcast.txt', 'w') as broadcast_log_file:
        async for user in all_users:
            sts, msg = await send_msg(
                user_id=int(user['id']),
                message=broadcast_msg
            )
            if msg is not None:
                await broadcast_log_file.write(msg)
            if sts == 200:
                success += 1
            else:
                failed += 1
            if sts == 400:
                await db.delete_user(user['id'])
            done += 1
            if Broadcast_IDs.get(broadcast_id) is None:
                break
            else:
                Broadcast_IDs[broadcast_id].update(
                    dict(
                        current=done,
                        failed=failed,
                        success=success
                    )
                )
    if Broadcast_IDs.get(broadcast_id):
        Broadcast_IDs.pop(broadcast_id)
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await asyncio.sleep(3)
    await out.delete()
    if failed == 0:
        await m.reply_text(
            text=f"broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True
        )
    else:
        await m.reply_document(
            document='broadcast.txt',
            caption=f"broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True
        )
    os.remove('broadcast.txt')