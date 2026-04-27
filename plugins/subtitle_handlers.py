from helper.utils import auth_filter, auth_user, progress_for_pyrogram
from helper.helper_func import ftext
import os
import time
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper.ffmpeg import add_soft_subtitle, add_hard_subtitle
from helper.custom_listen import ListenerTimeout

LOGGER = logging.getLogger(__name__)

@Client.on_message(filters.command("sub") & auth_filter)
async def sub_handler(client, message):
    if not await auth_user(None, client, message):
        return await message.reply(ftext(client.reply_text))
    user_id = message.from_user.id
    reply = message.reply_to_message

    video_msg = None
    if reply and (reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))):
        video_msg = reply
    else:
        try:
            video_msg = await client.ask(
                chat_id=user_id,
                text="🎬 **Please send the video message you want to add subtitles to.**\n\nType /cancel to abort.",
                filters=(filters.video | (filters.document & filters.create(lambda _, __, m: m.document.mime_type and m.document.mime_type.startswith("video/")))),
                timeout=300
            )
            if video_msg.text and video_msg.text.lower() == "/cancel":
                return await video_msg.reply("🚫 **Subtitles task cancelled.**")
        except ListenerTimeout:
            return await message.reply_text("⏰ **Timeout! Please try again.**")

    # Now ask for subtitle file
    try:
        sub_msg = await client.ask(
            chat_id=user_id,
            text="📝 **Now please send the subtitle file (e.g., .srt, .ass, .vtt).**\n\nType /cancel to abort.",
            filters=filters.document,
            timeout=300
        )
        if sub_msg.text and sub_msg.text.lower() == "/cancel":
            return await sub_msg.reply("🚫 **Subtitles task cancelled.**")

        file_name = sub_msg.document.file_name or ""
        if not file_name.lower().endswith(('.srt', '.ass', '.vtt')):
            return await sub_msg.reply("❌ **Invalid subtitle file. Please send a .srt, .ass, or .vtt file.**")

        # Save to session for the callback
        client.subtitle_sessions[user_id] = {'video': video_msg, 'sub': sub_msg}

        await sub_msg.reply_text(
            "📝 **Subtitle file received. Choose the subtitle type:**",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Soft Sub", callback_data="sub_soft"),
                    InlineKeyboardButton("Hard Sub", callback_data="sub_hard")
                ],
                [
                    InlineKeyboardButton("Cancel", callback_data="close")
                ]
            ]),
            quote=True
        )
    except ListenerTimeout:
        return await message.reply_text("⏰ **Timeout! Please try again.**")

@Client.on_callback_query(filters.regex("^sub_"))
async def subtitle_callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in client.subtitle_sessions:
        return await query.answer("Session expired. Please start again.", show_alert=True)

    action = query.data.split("_")[1]
    session = client.subtitle_sessions[user_id]
    video_msg = session['video']
    sub_msg = session['sub']

    await query.message.delete()
    status_msg = await client.send_message(user_id, "Processing...")

    # Create temporary directory for processing
    task_dir = f"downloads/sub_{user_id}_{int(time.time())}"
    os.makedirs(task_dir, exist_ok=True)

    try:
        # Download video
        await status_msg.edit("Downloading video...")

        video_file = video_msg.video or video_msg.document
        video_ext = ".mp4"
        if hasattr(video_file, "file_name") and video_file.file_name:
            if "." in video_file.file_name:
                video_ext = "." + video_file.file_name.rsplit(".", 1)[-1]

        video_path = await client.download_media(
            video_msg,
            file_name=os.path.join(task_dir, f"video{video_ext}"),
            progress=progress_for_pyrogram,
            progress_args=("Downloading video...", status_msg, time.time())
        )

        # Download subtitle
        await status_msg.edit("Downloading subtitle...")

        sub_ext = ".srt"
        if sub_msg.document.file_name and "." in sub_msg.document.file_name:
            sub_ext = "." + sub_msg.document.file_name.rsplit(".", 1)[-1]

        sub_path = await client.download_media(
            sub_msg,
            file_name=os.path.join(task_dir, f"subtitle{sub_ext}"),
            progress=progress_for_pyrogram,
            progress_args=("Downloading subtitle...", status_msg, time.time())
        )

        output_path = os.path.join(task_dir, "output.mkv")

        if action == "soft":
            await status_msg.edit("Applying soft subtitle (muxing)...")
            success, error = await add_soft_subtitle(client, status_msg, video_path, sub_path, output_path)
        else:
            await status_msg.edit("Applying hard subtitle (encoding)... This may take a while.")
            success, error = await add_hard_subtitle(client, status_msg, video_path, sub_path, output_path)

        if not success:
            return await status_msg.edit(f"❌ Error: {error}")

        # Upload processed file
        await status_msg.edit("Uploading processed video...")

        caption = "✅ **Subtitle Applied Successfully!**"

        await client.send_video(
            user_id,
            video=output_path,
            caption=caption,
            progress=progress_for_pyrogram,
            progress_args=("Uploading...", status_msg, time.time())
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"❌ An error occurred: {e}")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(task_dir, ignore_errors=True)
        if user_id in client.subtitle_sessions:
            del client.subtitle_sessions[user_id]
