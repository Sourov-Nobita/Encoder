from helper.utils import auth_filter
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.helper_func import encode, get_message_id, ftext, flbl
import asyncio

@Client.on_message(filters.command("genlink") & auth_filter)
async def genlink_cmd(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))

    if not message.reply_to_message:
        return await message.reply(ftext("❌ <b>Please reply to a message from the DB channel or a link to generate a sharing link.</b>"))

    chat_id, msg_id = await get_message_id(client, message.reply_to_message)
    if not chat_id or chat_id == 0:
        return await message.reply(ftext("❌ <b>Could not extract message ID. Make sure it's from the Dump channel or a valid link.</b>"))

    base64_string = await encode(f"single_{chat_id}_{msg_id}")
    link = f"https://t.me/{client.username}?start={base64_string}"

    await message.reply(ftext(f"✅ <b>Generated Single Link:</b>\n\n<code>{link}</code>"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(flbl("Get File"), url=link)]]))

@Client.on_message(filters.command("batch") & auth_filter)
async def batch_cmd(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))

    if len(message.command) < 2:
        # Ask for IDs via prompt
        prompt = await message.reply(ftext("<blockquote><b>Send the range of messages in format:</b>\n<code>start_link - end_link</code>\nor reply to two messages.</blockquote>"))
        try:
            res = await client.listen(chat_id=message.from_user.id, filters=filters.text, timeout=60)
            text = res.text
            if " - " in text:
                links = text.split(" - ")
                # Mock messages to use get_message_id
                m1 = Message(text=links[0].strip(), client=client)
                m2 = Message(text=links[1].strip(), client=client)
                c1, s1 = await get_message_id(client, m1)
                c2, s2 = await get_message_id(client, m2)
                if not (c1 and c2 and c1 == c2):
                    return await res.reply(ftext("❌ <b>Invalid links or different channels.</b>"))
                start_id, end_id = min(s1, s2), max(s1, s2)
                channel_id = c1
            else:
                return await res.reply(ftext("❌ <b>Invalid format.</b>"))
        except Exception as e:
            return await message.reply(ftext(f"❌ <b>Error:</b> {e}"))
    else:
        # Assume command format: /batch link1 link2
        try:
            links = message.command[1:]
            if len(links) < 2:
                return await message.reply(ftext("❌ <b>Provide two links.</b>"))
            m1 = Message(text=links[0], client=client)
            m2 = Message(text=links[1], client=client)
            c1, s1 = await get_message_id(client, m1)
            c2, s2 = await get_message_id(client, m2)
            if not (c1 and c2 and c1 == c2):
                return await message.reply(ftext("❌ <b>Invalid links or different channels.</b>"))
            start_id, end_id = min(s1, s2), max(s1, s2)
            channel_id = c1
        except Exception as e:
             return await message.reply(ftext(f"❌ <b>Error:</b> {e}"))

    base64_string = await encode(f"batch_{channel_id}_{start_id}_{end_id}")
    link = f"https://t.me/{client.username}?start={base64_string}"

    await message.reply(ftext(f"✅ <b>Generated Batch Link ({end_id - start_id + 1} files):</b>\n\n<code>{link}</code>"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(flbl("Get Files"), url=link)]]))
