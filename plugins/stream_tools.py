from helper.utils import auth_filter
import os
import time
import asyncio
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message
from helper.utils import progress_for_pyrogram, semaphore, add_task, remove_task, auth_user
from helper.ffmpeg import extract_all_subtitles, extract_all_audios, remove_all_subtitles, remove_all_audios
from helper.helper_func import ftext, flbl
from helper.anime_utils import get_thumbnail

@Client.on_message(filters.command(["extract_sub", "extract_audio", "remove_sub", "remove_audio"]) & auth_filter)
async def stream_tools_handler(client: Client, message: Message):
    if not await auth_user(None, client, message):
        reply_text = getattr(client, "reply_text", "❌ **This command is for Admins only!**")
        return await message.reply(ftext(reply_text))

    command = message.command[0].lower()
    reply = message.reply_to_message

    video_msg = None
    if reply and (reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))):
        video_msg = reply
    else:
        return await message.reply(ftext(f"❌ **Please reply to a video file to use /{command}.**"))

    user_id = message.from_user.id if message.from_user else message.chat.id
    task_id = f"{command}_{user_id}_{int(time.time())}"
    add_task(user_id, task_id, client=client)

    async with semaphore:
        await process_stream_tool(client, video_msg, command, user_id, task_id)

async def process_stream_tool(client, video_msg, command, user_id, task_id):
    status_msg = await client.send_message(user_id, ftext("<blockquote><b>Initializing...</b></blockquote>"))

    task_dir = f"downloads/{task_id}"
    os.makedirs(task_dir, exist_ok=True)

    try:
        video_file = video_msg.video or video_msg.document
        filename = video_file.file_name or "video.mp4"
        video_ext = os.path.splitext(filename)[1] or ".mp4"
        video_path = os.path.join(task_dir, f"input{video_ext}")

        await status_msg.edit(ftext(f"<blockquote>‣ <b>Status :</b> <i>Downloading...</i></blockquote>"))

        dl_path = await client.download_media(
            video_msg,
            file_name=video_path,
            progress=progress_for_pyrogram,
            progress_args=(f"Downloading {filename}", status_msg, time.time())
        )

        if not dl_path:
            return await status_msg.edit(ftext("❌ **Download failed!**"))

        if command == "extract_sub":
            await status_msg.edit(ftext("<blockquote>‣ <b>Status :</b> <i>Extracting Subtitles...</i></blockquote>"))
            success, result = await extract_all_subtitles(dl_path, task_dir)
            if success:
                for file in result:
                    await status_msg.edit(ftext(f"<blockquote>‣ <b>Status :</b> <i>Uploading {os.path.basename(file)}...</i></blockquote>"))
                    await client.send_document(user_id, document=file)
                await status_msg.edit(ftext("✅ **All subtitles extracted and uploaded successfully!**"))
            else:
                await status_msg.edit(ftext(f"❌ **Error:** {result}"))

        elif command == "extract_audio":
            await status_msg.edit(ftext("<blockquote>‣ <b>Status :</b> <i>Extracting Audios...</i></blockquote>"))
            success, result = await extract_all_audios(dl_path, task_dir)
            if success:
                for file in result:
                    await status_msg.edit(ftext(f"<blockquote>‣ <b>Status :</b> <i>Uploading {os.path.basename(file)}...</i></blockquote>"))
                    await client.send_audio(user_id, audio=file)
                await status_msg.edit(ftext("✅ **All audios extracted and uploaded successfully!**"))
            else:
                await status_msg.edit(ftext(f"❌ **Error:** {result}"))

        elif command == "remove_sub":
            await status_msg.edit(ftext("<blockquote>‣ <b>Status :</b> <i>Removing Subtitles...</i></blockquote>"))
            output_path = os.path.join(task_dir, f"no_sub_{filename}")
            success, error = await remove_all_subtitles(dl_path, output_path)
            if success:
                await status_msg.edit(ftext("<blockquote>‣ <b>Status :</b> <i>Uploading...</i></blockquote>"))
                thumb_path = await get_thumbnail(client, user_id, video_msg, task_dir)
                await client.send_video(user_id, video=output_path, thumb=thumb_path, caption=f"✅ **Subtitles removed from {filename}**")
                await status_msg.delete()
            else:
                await status_msg.edit(ftext(f"❌ **Error:** {error}"))

        elif command == "remove_audio":
            await status_msg.edit(ftext("<blockquote>‣ <b>Status :</b> <i>Removing Audios...</i></blockquote>"))
            output_path = os.path.join(task_dir, f"no_audio_{filename}")
            success, error = await remove_all_audios(dl_path, output_path)
            if success:
                await status_msg.edit(ftext("<blockquote>‣ <b>Status :</b> <i>Uploading...</i></blockquote>"))
                thumb_path = await get_thumbnail(client, user_id, video_msg, task_dir)
                await client.send_video(user_id, video=output_path, thumb=thumb_path, caption=f"✅ **Audios removed from {filename}**")
                await status_msg.delete()
            else:
                await status_msg.edit(ftext(f"❌ **Error:** {error}"))

    except Exception as e:
        await status_msg.edit(ftext(f"❌ **An error occurred:** {e}"))
    finally:
        shutil.rmtree(task_dir, ignore_errors=True)
        remove_task(user_id, task_id, client=client)
