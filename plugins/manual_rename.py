from helper.utils import auth_filter
import os
from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from helper.helper_func import ftext, flbl
from helper.custom_listen import ListenerTimeout
from plugins.auto_rename import process_file

@Client.on_message(filters.command("rename") & auth_filter)
async def rename_command(bot, message):
    if not message.reply_to_message:
        return await message.reply_text(ftext("Please reply to a media file to rename it."))

    file_msg = message.reply_to_message
    if not (file_msg.document or file_msg.video or file_msg.audio):
        return await message.reply_text(ftext("Please reply to a valid media file (document, video, or audio)."))

    await start_manual_rename(bot, file_msg)

@Client.on_callback_query(filters.regex('^rename$'))
async def rename(bot, update):
    file_msg = update.message.reply_to_message
    if not file_msg:
        try:
            msg = await bot.get_messages(update.message.chat.id, update.message.id)
            file_msg = msg.reply_to_message
        except Exception:
            file_msg = None

    if not file_msg:
        return await update.answer("Original message not found!", show_alert=True)

    await update.message.delete()
    await start_manual_rename(bot, file_msg)

async def start_manual_rename(bot, file_msg):
    user_id = file_msg.from_user.id if file_msg.from_user else file_msg.chat.id
    try:
        res = await bot.ask(
            chat_id=user_id,
            text=ftext("__Please Enter New File Name..__\n\nType /cancel to abort."),
            filters=filters.text,
            timeout=300,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(flbl("Cancel"), callback_data="close")]])
        )

        if res.text and res.text.lower() == "/cancel":
            return await res.reply(ftext("🚫 **Rename task cancelled.**"))

        new_name = res.text
        media = getattr(file_msg, file_msg.media.value)

        # Get original extension
        if hasattr(media, 'file_name') and media.file_name and "." in media.file_name:
            extn = media.file_name.rsplit('.', 1)[-1]
        else:
            # Fallback based on mime_type
            mime = getattr(media, "mime_type", "")
            if "video" in mime: extn = "mp4"
            elif "audio" in mime: extn = "mp3"
            else: extn = "mkv"

        # Check if new name already has the correct extension
        if not new_name.lower().endswith(f".{extn.lower()}"):
            new_name = new_name + "." + extn

        # Store the new name and original message ID temporarily in the database
        await bot.mongodb.set_temp_name(user_id, new_name)
        await bot.mongodb.set_user_setting(user_id, "temp_msg_id", file_msg.id)

        # Define buttons for output type selection
        buttons = [
            [InlineKeyboardButton(flbl("Document"), callback_data="upload_document")]
        ]
        if file_msg.video or (file_msg.document and file_msg.document.mime_type and file_msg.document.mime_type.startswith("video/")):
            buttons.append([InlineKeyboardButton(flbl("Video"), callback_data="upload_video")])
        elif file_msg.audio:
            buttons.append([InlineKeyboardButton(flbl("Audio"), callback_data="upload_audio")])

        buttons.append([InlineKeyboardButton(flbl("Cancel"), callback_data="close")])

        await bot.send_message(
            chat_id=user_id,
            text=ftext(f"**Select The Output File Type**\n\n**• File Name :-** `{new_name}`"),
            reply_to_message_id=file_msg.id,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except ListenerTimeout:
        await bot.send_message(user_id, ftext("⏰ **Timeout! Please try again.**"))

@Client.on_callback_query(filters.regex("^upload_"))
async def doc(bot, update):
    # Extract type from callback data
    type = update.data.split("_")[1]
    user_id = update.from_user.id

    # Retrieve the custom name from the database
    custom_name = await bot.mongodb.get_temp_name(user_id)
    if not custom_name:
        return await update.answer("Session expired or invalid. Please try again.", show_alert=True)

    msg_id = await bot.mongodb.get_user_setting(user_id, "temp_msg_id")
    if not msg_id:
        return await update.answer("Session expired or invalid. Please try again.", show_alert=True)

    file = await bot.get_messages(update.message.chat.id, msg_id)

    if not file or not (file.document or file.video or file.audio):
        return await update.answer("Original file message not found or invalid!", show_alert=True)

    await update.message.delete()
    await process_file(bot, file, user_id, custom_name=custom_name, custom_type=type)
