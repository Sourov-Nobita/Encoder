from helper.utils import auth_filter
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType
from helper.ffencoder import FFEncoder
from helper.tguploader import TgUploader
from helper.helper_func import ftext, flbl
from helper.anime_utils import sans_fonts, convertBytes, convertTime, get_thumbnail
from helper.utils import semaphore, add_task, remove_task, auth_user, is_video
import time
import random
import string
from config import Var

@Client.on_message(filters.command("encode") & auth_filter)
async def encode_cmd(client: Client, message: Message):
    # Admin only OR Authorized Group
    if not await auth_user(None, client, message):
        return await message.reply(ftext(client.reply_text))

    if not (message.reply_to_message and is_video(message.reply_to_message)):
        return await message.reply(ftext("❌ <b>Please reply to a video or document to encode.</b>"))

    # Auto-start if user has auto_encode ON (independent of global bot_mode when /encode is used)
    user_id = message.from_user.id if message.from_user else message.chat.id
    auto_encode = await client.mongodb.get_user_setting(user_id, "auto_encode", False)

    if auto_encode:
        quality = await client.mongodb.get_user_setting(user_id, "encode_quality")
        if not quality:
            quality = getattr(client, "encode_quality", "all")
        return await start_encoding(client, message.reply_to_message, quality, user_id=user_id)

    msg = ftext("<blockquote><b>⚙️ Encode Menu</b></blockquote>\nChoose the quality you want to encode the file to:")

    buttons = [
        [InlineKeyboardButton(flbl("480p"), callback_data="enc_480"), InlineKeyboardButton(flbl("720p"), callback_data="enc_720")],
        [InlineKeyboardButton(flbl("1080p"), callback_data="enc_1080"), InlineKeyboardButton(flbl("All"), callback_data="enc_all")],
        [InlineKeyboardButton(flbl("Close"), callback_data="close")]
    ]

    menu_msg = await message.reply(msg, reply_markup=InlineKeyboardMarkup(buttons))
    client.encode_tasks[menu_msg.id] = (message.reply_to_message.id, message.chat.id)

@Client.on_callback_query(filters.regex(r"^enc_(480|720|1080|all)$"))
async def start_encoding_cb(client: Client, query: CallbackQuery):
    # Retrieve the original message ID and chat ID from our tasks dictionary
    task_info = client.encode_tasks.get(query.message.id)
    original_msg_id, original_chat_id = task_info if task_info else (None, None)

    if not original_msg_id:
         # Fallback check if menu message was a reply to original message
         if query.message.reply_to_message:
             replied_msg = query.message.reply_to_message
             if is_video(replied_msg):
                 original_msg_id = replied_msg.id
                 original_chat_id = query.message.chat.id
             elif replied_msg.reply_to_message and is_video(replied_msg.reply_to_message):
                 original_msg_id = replied_msg.reply_to_message.id
                 original_chat_id = query.message.chat.id

    if not original_msg_id:
        return await query.message.edit(ftext("❌ <b>Original message not found!</b>"))

    # Permission check: If private, must be admin. If group, anyone can start their own or admin can start any.
    if query.message.chat.type == ChatType.PRIVATE and query.from_user.id not in client.admins:
        return await query.answer("Admin only!", show_alert=True)

    quality = query.data.split("_")[1]

    try:
        replied_msg = await client.get_messages(original_chat_id, original_msg_id)
    except Exception as e:
        return await query.message.edit(ftext(f"❌ <b>Error retrieving original message:</b> {e}"))

    if not replied_msg or not is_video(replied_msg):
        return await query.message.edit(ftext("❌ <b>Original file not found!</b>"))

    await query.message.delete()
    client.encode_tasks.pop(query.message.id, None)

    await start_encoding(client, replied_msg, quality, user_id=query.from_user.id)

async def start_encoding(client: Client, message: Message, quality: str, user_id: int = None):
    user_id = user_id or (message.from_user.id if message.from_user else None)

    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    task_id = f"enc_{user_id}_{int(time.time())}_{random_str}"
    add_task(user_id, task_id, client=client)

    async with semaphore:
        await _start_encoding_process(client, message, quality, user_id, task_id)

async def _start_encoding_process(client: Client, message: Message, quality: str, user_id: int, task_id: str):
    status_msg = None
    download_path = None
    try:
        upload_mode = await client.mongodb.get_upload_mode(user_id)
        if upload_mode == "pm":
            target_chat_id = user_id
        elif upload_mode == "channel":
            target_chat_id = await client.mongodb.get_upload_channel(user_id) or message.chat.id
        else:
            target_chat_id = message.chat.id

        upload_to = target_chat_id
        if upload_mode == "channel" and not (await client.mongodb.get_upload_channel(user_id)):
            upload_to = getattr(client, "dump_channel", None) or target_chat_id

        status_msg = await client.send_message(message.chat.id, ftext("<blockquote><b>Initializing...</b></blockquote>"), reply_to_message_id=message.id)

        file = message.video or message.document
        filename = getattr(file, "file_name", "video.mp4") or "video.mp4"

        download_path = os.path.join("downloads", str(user_id or "shared"), filename)
        os.makedirs(os.path.dirname(download_path), exist_ok=True)

        # Download
        await edit_status(status_msg, filename, "Downloading")

        start_time = asyncio.get_event_loop().time()
        last_update = 0

        async def progress(current, total):
            nonlocal last_update
            now = asyncio.get_event_loop().time()
            if now - last_update < 5:
                return
            last_update = now

            percent = (current / total) * 100
            bar = "█" * int(percent / 5) + "▒" * (20 - int(percent / 5))

            diff = now - start_time
            speed = current / diff if diff > 0 else 0
            eta = (total - current) / speed if speed > 0 else 0

            text = f"""‣ <b>{sans_fonts('File Name')} :</b>
<blockquote><b><i>{filename}</i></b></blockquote>

<blockquote>‣ <b>{sans_fonts('Status')} :</b> <i>{sans_fonts('Downloading')}</i>
<code>[{bar}]</code> {percent:.2f}% </blockquote>

<blockquote>‣ <b>{sans_fonts('Size')} :</b> {convertBytes(current)} {sans_fonts('out of')} ~ {convertBytes(total)}
‣ <b>{sans_fonts('Speed')} :</b> {convertBytes(speed)}/s
‣ <b>{sans_fonts('Time Took')} :</b> {convertTime(int(diff))}
‣ <b>{sans_fonts('Time Left')} :</b> {convertTime(int(eta))} </blockquote>"""
            try:
                from helper.anime_utils import editMessage
                await editMessage(status_msg, text)
            except Exception:
                pass

        dl_path = await message.download(file_name=download_path, progress=progress)

        if not dl_path:
            return await status_msg.edit(ftext("❌ <b>Download failed!</b>"))

        if quality == "all":
            qualities = ["480", "720", "1080"]
        else:
            qualities = [quality]

        metadata_status = getattr(client, "metadata_status", False)
        metadata_val = None
        if user_id:
            metadata_status = await client.mongodb.get_metadata_status(user_id) or metadata_status
            metadata_val = await client.mongodb.get_metadata(user_id)

        task_dir = os.path.dirname(dl_path)
        thumb_path = await get_thumbnail(client, user_id, message, task_dir)

        for idx, q in enumerate(qualities):
            # Encode
            await edit_status(status_msg, filename, f"Encoding {q}p")

            out_name = f"{os.path.splitext(filename)[0]}_{q}p.mkv"
            encoder = FFEncoder(
                status_msg, dl_path, out_name, q,
                count=f"{idx+1}/{len(qualities)}",
                metadata_status=metadata_status,
                metadata=metadata_val,
                user_id=user_id
            )
            encoded_path = await encoder.start_encode()

            if not encoded_path:
                continue

            # Upload
            await edit_status(status_msg, out_name, f"Uploading {q}p")
            uploader = TgUploader(status_msg, client)
            uploaded_file = await uploader.upload(encoded_path, q, target_chat_id=upload_to, thumb=thumb_path)

            # Copy to dump if not already uploaded there
            dump_channel = getattr(client, "dump_channel", None)
            if dump_channel and upload_to != dump_channel:
                if uploaded_file and not uploaded_file.empty:
                    try: await uploaded_file.copy(dump_channel)
                    except: pass

            if os.path.exists(encoded_path):
                os.remove(encoded_path)

        await status_msg.edit(ftext(f"✅ <b>Encoding completed for {filename}!</b>"))

        if os.path.exists(dl_path):
            os.remove(dl_path)

    except Exception as e:
        if status_msg:
            await status_msg.edit(ftext(f"❌ <b>Error:</b> <code>{str(e)}</code>"))
        if download_path and os.path.exists(download_path):
            os.remove(download_path)
    finally:
        remove_task(user_id, task_id, client=client)

async def edit_status(msg, name, status):
    text = f"‣ <b>{sans_fonts('File Name')} :</b>\n<blockquote><b><i>{name}</i></b></blockquote>\n\n<blockquote><i>{status}...</i></blockquote>"
    try:
        from helper.anime_utils import editMessage
        await editMessage(msg, ftext(text))
    except Exception:
        pass
