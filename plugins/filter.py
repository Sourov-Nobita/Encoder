from helper.utils import auth_filter
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from helper.helper_func import ftext, flbl, is_admin
from pyrogram.enums import ChatType
from helper.custom_listen import ListenerTimeout

@Client.on_message(filters.command("filter") & auth_filter)
async def add_filter_handler(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if not message.reply_to_message:
        await message.reply(ftext("Reply to a message to set it as a filter reply"))
        return

    replied_msg = message.reply_to_message

    prompt = await message.reply(ftext("Now send the keyword for this filter:"))
    try:
        res = await client.listen(chat_id=message.chat.id, user_id=message.from_user.id, timeout=300)
        keyword = (res.text or "").lower()

        await client.mongodb.database_obj.filters.update_one(
            {"chat_id": message.chat.id, "keyword": keyword},
            {"$set": {
                "reply_chat_id": replied_msg.chat.id,
                "reply_msg_id": replied_msg.id
            }},
            upsert=True
        )
        await message.reply(ftext(f"Filter for '{keyword}' has been set"))
    except ListenerTimeout:
        await prompt.edit_text(ftext("Timeout! Please try again."))
    except Exception as e:
        await message.reply(ftext(f"Error: {e}"))

@Client.on_message(filters.command("stop") & auth_filter)
async def stop_filter_handler(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if len(message.command) < 2:
        await message.reply(ftext("Usage: /stop <keyword>"))
        return

    keyword = message.command[1].lower()
    res = await client.mongodb.database_obj.filters.delete_one({"chat_id": message.chat.id, "keyword": keyword})
    if res.deleted_count > 0:
        await message.reply(ftext(f"Filter for '{keyword}' removed"))
    else:
        await message.reply(ftext(f"No filter found for '{keyword}'"))

@Client.on_message(filters.command("filters") & auth_filter)
async def list_filters_handler(client: Client, message: Message):
    cursor = client.mongodb.database_obj.filters.find({"chat_id": message.chat.id})
    filters_list = await cursor.to_list(length=100)

    if not filters_list:
        await message.reply(ftext("No active filters"))
        return

    text = f"<b>{ftext('Active Filters')}:</b>\n"
    for f in filters_list:
        text += f"- <code>{f['keyword']}</code>\n"
    await message.reply(text)

@Client.on_message(filters.command("stopall") & auth_filter)
async def stopall_filters_handler(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    await client.mongodb.database_obj.filters.delete_many({"chat_id": message.chat.id})
    await message.reply(ftext("All filters removed"))

@Client.on_message((filters.text | filters.caption) & ~filters.regex(r"^/"), group=2)
async def filter_trigger_handler(client: Client, message: Message):
    text = (message.text or message.caption or "").lower()
    if not text:
        return

    cursor = client.mongodb.database_obj.filters.find({"chat_id": message.chat.id})
    async for f in cursor:
        pattern = r"\b" + re.escape(f["keyword"]) + r"\b"
        if re.search(pattern, text):
            try:
                await client.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=f["reply_chat_id"],
                    message_id=f["reply_msg_id"],
                    reply_to_message_id=message.id
                )
            except Exception as e:
                client.LOGGER(__name__, client.name).error(f"Filter error: {e}")
            break
