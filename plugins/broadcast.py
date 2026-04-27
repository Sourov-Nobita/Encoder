from helper.utils import auth_filter
from helper.helper_func import ftext
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.raw.types import MessageActionPinMessage
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant, Forbidden, PeerIdInvalid, ChatAdminRequired
import asyncio

async def delete_message_after_delay(message, delay):
    """
    A helper coroutine that waits for a specified delay and then deletes the message.
    Runs in the background without blocking.
    """
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        print(f"Could not delete message {message.id} after delay: {e}")
        pass

@Client.on_message(filters.command('users') & auth_filter)
async def user_count(client, message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))
    total_users = await client.mongodb.full_userbase()
    await message.reply(ftext(f"**{len(total_users)} Users are using this bot currently!**"))

@Client.on_message(filters.command('broadcast') & auth_filter)
async def send_text(client, message):
    user_id = message.from_user.id
    if user_id not in client.admins:
        return await message.reply(ftext(client.reply_text))

    if True:
        
        if message.reply_to_message:
            if message.reply_to_message.empty:
                return await message.reply(ftext("❌ **Cannot broadcast an empty message.**"))
            query = await client.mongodb.full_userbase()
            broadcast_msg = message.reply_to_message
            total = 0
            successful = 0
            blocked = 0
            deleted = 0
            unsuccessful = 0
            
            pls_wait = await message.reply(ftext("<blockquote><i>Broadcasting Message.. This will Take Some Time</i></blockquote>"), parse_mode=ParseMode.HTML)
            for chat_id in query:
                try:
                    while True:
                        try:
                            await broadcast_msg.copy(chat_id)
                            successful += 1
                            break
                        except FloodWait as e:
                            await asyncio.sleep(e.value + 1)
                except UserIsBlocked:
                    await client.mongodb.del_user(chat_id)
                    blocked += 1
                except InputUserDeactivated:
                    await client.mongodb.del_user(chat_id)
                    deleted += 1
                except Exception as e:
                    print(f"Failed to send message to {chat_id}: {e}")
                    unsuccessful += 1
                    pass
                total += 1
            
            status = ftext(f"""<blockquote><b><u>Broadcast Completed</u></b></blockquote>
    <blockquote expandable><b>Total Users :</b> <code>{total}</code>
    <b>Successful :</b> <code>{successful}</code>
    <b>Blocked Users :</b> <code>{blocked}</code>
    <b>Deleted Accounts :</b> <code>{deleted}</code>
    <b>Unsuccessful :</b> <code>{unsuccessful}</code></blockquote>""")
            
            return await pls_wait.edit(status, parse_mode=ParseMode.HTML)
    
        else:
            msg = await message.reply(ftext("Use This Command As A Reply To Any Telegram Message Without Any Spaces."))
            await asyncio.sleep(8)
            await msg.delete()

@Client.on_message(filters.command('dbroadcast') & auth_filter)
async def deletable_broadcast(client, message):
    """Handles /dbroadcast command with an auto-delete timer."""
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))

    if not message.reply_to_message:
        return await message.reply(ftext("<b>Please reply to a message to broadcast it with a timer.</b>"), parse_mode=ParseMode.HTML)

    if message.reply_to_message.empty:
        return await message.reply(ftext("❌ **Cannot broadcast an empty message.**"))

    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            raise ValueError()
        timer_seconds = int(parts[1])
        if timer_seconds <= 0:
            raise ValueError()
    except (ValueError, IndexError):
        return await message.reply(
            ftext("<b>Invalid format. Please provide a positive number of seconds for the timer.</b>\n\n"
            "<b>Usage:</b> <code>/dbroadcast 3600</code> (deletes after 1 hour)"),
            parse_mode=ParseMode.HTML
        )

    query = await client.mongodb.full_userbase()
    broadcast_msg = message.reply_to_message
    total = 0
    successful = 0
    blocked = 0
    deleted = 0
    unsuccessful = 0
    
    pls_wait = await message.reply(
        ftext(f"<blockquote><i>Broadcasting message with a {timer_seconds}-second auto-delete timer...</i></blockquote>"),
        parse_mode=ParseMode.HTML
    )
    
    for chat_id in query:
        try:
            while True:
                try:
                    sent_msg = await broadcast_msg.copy(chat_id)
                    client.create_background_task(delete_message_after_delay(sent_msg, timer_seconds))
                    successful += 1
                    break
                except FloodWait as e:
                    await asyncio.sleep(e.value + 1)
        except UserIsBlocked:
            await client.mongodb.del_user(chat_id)
            blocked += 1
        except InputUserDeactivated:
            await client.mongodb.del_user(chat_id)
            deleted += 1
        except Exception as e:
            print(f"Failed to send deletable broadcast to {chat_id}: {e}")
            unsuccessful += 1
        total += 1
            
    status = ftext(f"""<blockquote><b><u>Deletable Broadcast Completed</u></b></blockquote>
<blockquote expandable><b>Timer Set:</b> <code>{timer_seconds} seconds</code>
<b>Total Users:</b> <code>{total}</code>
<b>Successful:</b> <code>{successful}</code>
<b>Blocked Users:</b> <code>{blocked}</code>
<b>Deleted Accounts:</b> <code>{deleted}</code>
<b>Unsuccessful:</b> <code>{unsuccessful}</code></blockquote>""")
    
    await pls_wait.edit(status, parse_mode=ParseMode.HTML)


@Client.on_message(filters.command('pbroadcast') & auth_filter)
async def pin_bdcst_text(client, message):
    user_id = message.from_user.id
    if user_id not in client.admins:
        return await message.reply(ftext(client.reply_text))

    if True:
        if message.reply_to_message:
            if message.reply_to_message.empty:
                return await message.reply(ftext("❌ **Cannot broadcast an empty message.**"))
            query = await client.mongodb.full_userbase()
            broadcast_msg = message.reply_to_message
            total = 0
            successful = 0
            blocked = 0
            deleted = 0
            unsuccessful = 0
    
            pls_wait = await message.reply(ftext("<blockquote><i>Broadcasting Message.. This will Take Some Time</i></blockquote>"), parse_mode=ParseMode.HTML)
            
            for chat_id in query:
                try:
                    while True:
                        try:
                            sent_msg = await broadcast_msg.copy(chat_id)
                            successful += 1
                            await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
                            break
                        except FloodWait as e:
                            await asyncio.sleep(e.value + 1)
                except UserIsBlocked:
                    await client.mongodb.del_user(chat_id)
                    blocked += 1
                except InputUserDeactivated:
                    await client.mongodb.del_user(chat_id)
                    deleted += 1
                except Exception as e:
                    print(f"Failed to send message to {chat_id}: {e}")
                    unsuccessful += 1
                total += 1
    
            status = ftext(f"""<blockquote><b><u>Broadcast Completed</u></b></blockquote>
    <b>Total Users :</b> <code>{total}</code>
    <b>Successful :</b> <code>{successful}</code>
    <b>Blocked Users :</b> <code>{blocked}</code>
    <b>Deleted Accounts :</b> <code>{deleted}</code>
    <b>Unsuccessful :</b> <code>{unsuccessful}</code>""")
    
            return await pls_wait.edit(status, parse_mode=ParseMode.HTML)
    
        else:
            msg = await message.reply(ftext("Use This Command As A Reply To Any Telegram Message Without Any Spaces."))
            await asyncio.sleep(8)
            await msg.delete()
