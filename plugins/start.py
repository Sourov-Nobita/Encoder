from helper.utils import auth_filter

from helper.helper_func import decode, force_sub, get_messages, ftext, flbl
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
import humanize
import asyncio
from datetime import datetime, timedelta
from plugins.others import send_start_message

@Client.on_message(filters.command('start'))
@force_sub
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not await client.mongodb.present_user(user_id):
        await client.mongodb.add_user(user_id)
    if await client.mongodb.is_banned(user_id):
        return await message.reply(ftext("**You have been banned!**"))

    text = message.text
    if len(text) <= 7:
        return await send_start_message(client, message)

    try:
        param = text.split(" ", 1)[1]
    except IndexError:
        return await send_start_message(client, message)

    base64_string = param

    try:
        decoded_string = await decode(base64_string)
    except Exception:
        return await message.reply(ftext("❌ Invalid or expired link."))

    is_single_file_link = False
    try:
        parts = decoded_string.split("_")
        command = parts[0]
        if command == "single":
            is_single_file_link = True
            channel_id, msg_ids = int(parts[1]), [int(parts[2])]
        elif command == "batch":
            if len(parts) == 4:
                channel_id, start_id, end_id = int(parts[1]), int(parts[2]), int(parts[3])
                msg_ids = list(range(start_id, end_id + 1))
            else:
                channel_id, msg_ids = await client.mongodb.get_batch(parts[1])
                if not (channel_id and msg_ids) and client.master_mongodb:
                    channel_id, msg_ids = await client.master_mongodb.get_batch(parts[1])
                if not (channel_id and msg_ids): return await message.reply("❌ This link has expired.")
        else:
            raise ValueError("Unsupported link format")
    except (IndexError, ValueError):
        return await message.reply(ftext("❌ Invalid or malformed file link."))

    temp_msg = await message.reply(ftext("<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>"), parse_mode=ParseMode.HTML)
    
    messages_to_send = await get_messages(client, channel_id, msg_ids)
    if not messages_to_send:
        return await temp_msg.edit(ftext("❌ <b>Content Not Found.</b> It may have been deleted."))
    
    await temp_msg.delete()

    sent_messages, failed_count = [], 0
    for msg in messages_to_send:
        if not msg or msg.empty:
            continue
        
        is_web_page = hasattr(msg, 'web_page') and msg.web_page is not None

        if msg.media and not is_web_page:
            final_caption = (msg.caption.html if msg.caption else "")
            
            try:
                sent_msg = await msg.copy(
                    chat_id=user_id,
                    caption=final_caption,
                )
                sent_messages.append(sent_msg)

            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
                try:
                    sent_msg = await msg.copy(user_id, caption=final_caption)
                    sent_messages.append(sent_msg)
                except Exception: failed_count += 1
            except Exception:
                failed_count += 1
        
        elif msg.text:
            try:
                sent_text = await client.send_message(user_id, msg.text.html, disable_web_page_preview=True)
                sent_messages.append(sent_text)
            except Exception:
                failed_count += 1
    
    if not sent_messages and not failed_count:
        await message.reply(ftext("No valid content found in the requested link(s)."))
        return

    if failed_count > 0:
        await client.send_message(user_id, ftext(f"⚠️ <b>Note:</b> {failed_count} item(s) could not be sent."))
    
