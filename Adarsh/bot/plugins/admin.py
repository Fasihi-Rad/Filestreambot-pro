# (c) @Fasihi-Rad
import os
import time
import string
import random
import asyncio
import aiofiles
import datetime
import re
import logging
from typing import Dict, List, Optional
from pathlib import Path

from pyrogram import filters, Client
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid, UserIsBlocked, ChatWriteForbidden

from Adarsh.utils.broadcast_helper import send_msg
from Adarsh.utils.database import Database
from Adarsh.bot import StreamBot
from Adarsh.vars import Var
from Adarsh.utils.human_readable import byte_to_human_read

logger = logging.getLogger(__name__)
db = Database(Var.DATABASE_URL, Var.NAME)
Broadcast_IDs: Dict[str, Dict[str, int]] = {}

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in Var.OWNER_ID

@StreamBot.on_message(filters.command("admin") & filters.private)
async def admin_commands(client: Client, message: Message) -> None:
    """Show admin commands list"""
    try:
        if not is_admin(message.from_user.id):
            await message.reply_text("❌ You are not authorized to use this command.")
            return
            
        admin_help = (
            f"👋 Hi {message.from_user.mention(style='md')}!\n\n"
            "🔧 **Admin Commands:**\n\n"
            "1️⃣ `/admin` - Show this help\n"
            "2️⃣ `/users` - Display total user count\n"
            "3️⃣ `/userslist` - Display all user names\n"
            "4️⃣ `/deluser <ID>` - Delete user\n"
            "5️⃣ `/banuser <ID>` - Ban user\n"
            "6️⃣ `/userinfo <ID>` - Display user info\n"
            "7️⃣ `/broadcast` - Broadcast message to all users\n"
            "8️⃣ `/cus <ID> <STATUS>` - Change user status\n\n"
            "📊 Use `/status` for bot statistics"
        )
        
        await message.reply_text(admin_help)
        logger.info(f"Admin {message.from_user.id} accessed admin commands")
        
    except Exception as e:
        logger.error(f"Error in admin command: {e}")
        await message.reply_text("❌ An error occurred while processing the command.")

@StreamBot.on_message(filters.command("users") & filters.private)
async def users_count(client: Client, message: Message) -> None:
    """Show total users count"""
    try:
        if not is_admin(message.from_user.id):
            await message.reply_text("❌ You are not authorized to use this command.")
            return
            
        total_users = await db.total_users_count()
        await message.reply_text(
            f"📊 **Database Statistics:**\n\n"
            f"👥 Total Users: **{total_users:,}**",
            quote=True
        )
        logger.info(f"Admin {message.from_user.id} checked user count: {total_users}")
        
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        await message.reply_text("❌ Failed to retrieve user count.")

@StreamBot.on_message(filters.command("userslist") & filters.private)
async def users_list(client: Client, message: Message) -> None:
    """Show all users list with pagination"""
    try:
        if not is_admin(message.from_user.id):
            await message.reply_text("❌ You are not authorized to use this command.")
            return
            
        status_msg = await message.reply_text(
            "⏳ **Fetching users list...**\n"
            "_This may take a few moments..._",
            quote=True
        )
        
        users_list: List[str] = []
        all_users = await db.get_all_users()
        
        if all_users is None:
            await status_msg.edit_text("❌ Failed to fetch users from database.")
            return
            
        user_count = 0
        async for user in all_users:
            user_count += 1
            name = user.get('name', 'Unknown')
            user_id = user.get('id', 'Unknown')
            users_list.append(f"[{name}](tg://user?id={user_id})")
            
            # Prevent message too long error - split into chunks
            if user_count % 50 == 0:
                current_list = users_list[-50:]
                chunk_text = f"👥 **Users ({user_count-49} - {user_count}):**\n\n" + "   ".join(current_list)
                await message.reply_text(chunk_text, quote=True)
        
        # Send remaining users
        if users_list:
            remaining_start = (user_count // 50) * 50 + 1
            remaining_users = users_list[remaining_start-1:] if remaining_start > 1 else users_list
            if remaining_users:
                final_text = f"👥 **Users ({remaining_start} - {user_count}):**\n\n" + "   ".join(remaining_users)
                await message.reply_text(final_text, quote=True)
        
        await status_msg.edit_text(f"✅ **Users list completed!**\n📊 Total users: **{user_count:,}**")
        logger.info(f"Admin {message.from_user.id} requested users list ({user_count} users)")
        
    except Exception as e:
        logger.error(f"Error getting users list: {e}")
        await message.reply_text("❌ Failed to retrieve users list.")
        
@StreamBot.on_message(filters.command("deluser") & filters.private)
async def delete_user(client: Client, message: Message) -> None:
    """Delete users from database"""
    try:
        if not is_admin(message.from_user.id):
            await message.reply_text("❌ You are not authorized to use this command.")
            return
            
        # Extract user IDs from command
        user_ids = re.findall(r"(\d+)", message.text)
        
        if not user_ids:
            await message.reply_text(
                "❌ **Invalid format!**\n\n"
                "**Usage:** `/deluser <user_id1> [user_id2] ...`\n"
                "**Example:** `/deluser 123456789` or `/deluser 123 456 789`"
            )
            return
        
        if len(user_ids) > 10:
            await message.reply_text("❌ You can delete maximum 10 users at once.")
            return
            
        status_msg = await message.reply_text(
            f"⏳ **Deleting users...**\n"
            f"👥 Users to delete: `{', '.join(user_ids)}`",
            quote=True
        )
        
        deleted_count = 0
        failed_count = 0
        results = []
        
        for user_id_str in user_ids:
            try:
                user_id = int(user_id_str)
                
                # Check if user exists first
                user_info = await db.user_info(user_id)
                if not user_info:
                    results.append(f"❌ User `{user_id}` not found")
                    failed_count += 1
                    continue
                
                # Delete user
                success = await db.delete_user(user_id)
                if success:
                    results.append(f"✅ User [{user_id}](tg://user?id={user_id}) deleted")
                    deleted_count += 1
                    logger.info(f"Admin {message.from_user.id} deleted user {user_id}")
                else:
                    results.append(f"❌ Failed to delete user `{user_id}`")
                    failed_count += 1
                    
            except ValueError:
                results.append(f"❌ Invalid user ID: `{user_id_str}`")
                failed_count += 1
            except Exception as e:
                logger.error(f"Error deleting user {user_id_str}: {e}")
                results.append(f"❌ Error deleting user `{user_id_str}`")
                failed_count += 1
        
        # Send results
        result_text = (
            f"🗑️ **Delete Users Complete**\n\n"
            f"✅ Deleted: **{deleted_count}**\n"
            f"❌ Failed: **{failed_count}**\n\n"
            + "\n".join(results)
        )
        
        await status_msg.edit_text(result_text)
        
    except Exception as e:
        logger.error(f"Error in delete user command: {e}")
        await message.reply_text("❌ An error occurred while deleting users.")

@StreamBot.on_message(filters.command("banuser") & filters.private)
async def ban_user(client: Client, message: Message) -> None:
    """Ban users from using the bot"""
    try:
        if not is_admin(message.from_user.id):
            await message.reply_text("❌ You are not authorized to use this command.")
            return
            
        # Extract user IDs from command
        user_ids = re.findall(r"(\d+)", message.text)
        
        if not user_ids:
            await message.reply_text(
                "❌ **Invalid format!**\n\n"
                "**Usage:** `/banuser <user_id1> [user_id2] ...`\n"
                "**Example:** `/banuser 123456789` or `/banuser 123 456 789`"
            )
            return
        
        if len(user_ids) > 10:
            await message.reply_text("❌ You can ban maximum 10 users at once.")
            return
            
        status_msg = await message.reply_text(
            f"⏳ **Banning users...**\n"
            f"👥 Users to ban: `{', '.join(user_ids)}`",
            quote=True
        )
        
        banned_count = 0
        failed_count = 0
        results = []
        
        for user_id_str in user_ids:
            try:
                user_id = int(user_id_str)
                
                # Check if user exists first
                user_info = await db.user_info(user_id)
                if not user_info:
                    results.append(f"❌ User `{user_id}` not found")
                    failed_count += 1
                    continue
                
                # Check if already banned
                if user_info.get('status') == 'banned':
                    results.append(f"⚠️ User [{user_id}](tg://user?id={user_id}) already banned")
                    continue
                
                # Ban user
                success = await db.ban_user(user_id)
                if success:
                    results.append(f"🔨 User [{user_id}](tg://user?id={user_id}) banned")
                    banned_count += 1
                    logger.info(f"Admin {message.from_user.id} banned user {user_id}")
                else:
                    results.append(f"❌ Failed to ban user `{user_id}`")
                    failed_count += 1
                    
            except ValueError:
                results.append(f"❌ Invalid user ID: `{user_id_str}`")
                failed_count += 1
            except Exception as e:
                logger.error(f"Error banning user {user_id_str}: {e}")
                results.append(f"❌ Error banning user `{user_id_str}`")
                failed_count += 1
        
        # Send results
        result_text = (
            f"🔨 **Ban Users Complete**\n\n"
            f"✅ Banned: **{banned_count}**\n"
            f"❌ Failed: **{failed_count}**\n\n"
            + "\n".join(results)
        )
        
        await status_msg.edit_text(result_text)
        
    except Exception as e:
        logger.error(f"Error in ban user command: {e}")
        await message.reply_text("❌ An error occurred while banning users.")

@StreamBot.on_message(filters.command("cus") & filters.private )
async def sts(c: Client, m: Message):
    user_id=m.from_user.id
    if user_id in Var.OWNER_ID:
        user_ids = re.findall(r"([\d]+)", m.text)
        new_status = re.findall(r"(subscribed|free|banned)", m.text)
        if new_status[0] == "banned" or new_status[0] == "subscribed" or new_status[0] == "free":
            await m.reply_text(text=f"<b>You want to chenge this user status</b>\nUsers : {user_ids}\nTo Status : {new_status[0]}", quote=True,)
            for user_id in user_ids:
                await db.change_user_status(user_id, new_status[0])
                await m.reply_text(text=f"<b>User [{user_id}](tg://user?id={user_ids}) status change to {new_status[0]}.</b>", quote=True)
        else:
            await m.reply_text(text=f"<b>Wrong Status</b>\n<b>Status : `banned` `subscribed` `free`</b>\nTry again !", quote=True)

@StreamBot.on_message(filters.command("userinfo") & filters.private )       
async def sts(c: Client, m: Message):
    user_id=m.from_user.id
    if user_id in Var.OWNER_ID:
        userinfo_ids = re.findall(r"([\d]+)", m.text)
        await m.reply_text(text=f"<b>It's may take several moment !</b>", quote=True)
        for userinfo_id in userinfo_ids:
            await db.update_user_link_limit(userinfo_id)
            user = await db.user_info(userinfo_id)
            if user:
                botstats = f'<b>User [{user["name"]}](tg://user?id={userinfo_ids}) Info : </b> \n\n' \
                    f'<b>Telegram ID:` {user["id"]}`</b>\n' \
                    f'<b>Name:</b> `{user["name"]}`\n' \
                    f'<b>Telegram Username:</b> `{user["telegram_username"]}`\n' \
                    f'<b>Status:</b> `{user["status"]}`\n' \
                    f'<b>Today Links Made:</b> `{user["link_made"]}`\n' \
                    f'<b>Today Download Size:</b> `{byte_to_human_read(user["total_download"])}`\n' \
                    f'<b>Join Date:</b> `{user["join_date"]}`\n'
            else:
                botstats = f"User {userinfo_id} dosen't exist."
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