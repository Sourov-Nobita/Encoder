from helper.utils import auth_filter
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from helper.helper_func import ftext, force_sub

FONTS_DIR = "fonts"

@Client.on_message(filters.command("add_font") & auth_filter)
@force_sub
async def add_font(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(getattr(client, "reply_text", "Admin only!")))

    if not (message.reply_to_message and message.reply_to_message.document):
        return await message.reply(ftext("❌ <b>Please reply to a .ttf or .otf font file!</b>"))

    doc = message.reply_to_message.document
    if not (doc.file_name.lower().endswith(".ttf") or doc.file_name.lower().endswith(".otf")):
        return await message.reply(ftext("❌ <b>Invalid font file! Only .ttf and .otf are supported.</b>"))

    os.makedirs(FONTS_DIR, exist_ok=True)
    status = await message.reply(ftext("<blockquote><b>Downloading font...</b></blockquote>"))

    file_path = os.path.join(FONTS_DIR, doc.file_name)
    if os.path.exists(file_path):
        return await status.edit(ftext(f"❌ <b>Font <code>{doc.file_name}</code> already exists!</b>"))

    await client.download_media(message.reply_to_message, file_name=file_path)
    await status.edit(ftext(f"✅ <b>Font <code>{doc.file_name}</code> added successfully!</b>"))

@Client.on_message(filters.command("list_font") & auth_filter)
@force_sub
async def list_fonts(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(getattr(client, "reply_text", "Admin only!")))

    if not os.path.exists(FONTS_DIR) or not os.listdir(FONTS_DIR):
        return await message.reply(ftext("❌ <b>No custom fonts found!</b>"))

    fonts = os.listdir(FONTS_DIR)
    text = "<blockquote><b>Custom Fonts List:</b></blockquote>\n\n"
    for idx, font in enumerate(fonts, 1):
        text += f"<code>{idx}.</code> <code>{font}</code>\n"

    await message.reply(ftext(text))
