from helper.utils import auth_filter
import aiohttp
import os
import logging
import time
from pyrogram import Client, filters
from helper.utils import progress_for_pyrogram, auth_user
from helper.helper_func import ftext, flbl

LOGGER = logging.getLogger(__name__)

async def upload_catbox(file_path):
    """Upload a file to catbox.moe."""
    url = "https://catbox.moe/user/api.php"
    file_name = os.path.basename(file_path)

    try:
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('reqtype', 'fileupload')
            data.add_field('fileToUpload', f, filename=file_name)

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        text = await response.text()
                        LOGGER.error(f"Catbox upload failed for {file_name} with status {response.status}: {text}")
    except Exception as e:
        LOGGER.error(f"Error in catbox upload for {file_name}: {e}")
    return None

async def upload_envs(file_path):
    """Upload a file to envs.sh."""
    url = "https://envs.sh"
    file_name = os.path.basename(file_path)

    try:
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=file_name)

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        text = await response.text()
                        LOGGER.error(f"Envs upload failed for {file_name} with status {response.status}: {text}")
    except Exception as e:
        LOGGER.error(f"Error in envs upload for {file_name}: {e}")
    return None

async def upload_uguu(file_path):
    """Upload a file to uguu.se."""
    url = "https://uguu.se/upload.php"
    file_name = os.path.basename(file_path)

    try:
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('files[]', f, filename=file_name)

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        if res_json.get("success"):
                            return res_json["files"][0]["url"]
                        else:
                            LOGGER.error(f"Uguu upload error for {file_name}: {res_json}")
                    else:
                        text = await response.text()
                        LOGGER.error(f"Uguu upload failed for {file_name} with status {response.status}: {text}")
    except Exception as e:
        LOGGER.error(f"Error in uguu upload for {file_name}: {e}")
    return None

@Client.on_message(filters.command("img") & auth_filter)
async def catbox_upload_handler(client, message):
    if not await auth_user(None, client, message):
        return await message.reply(ftext(getattr(client, "reply_text", "You are not authorized to use this command.")))

    reply = message.reply_to_message
    if not reply or not (reply.photo or reply.document or reply.video or reply.audio or reply.animation):
        return await message.reply_text("Please reply to a photo/file/video/audio/animation to upload it to Catbox.")

    msg = await message.reply_text("Downloading file to upload to Catbox...")

    try:
        file_path = await client.download_media(
            reply,
            progress=progress_for_pyrogram,
            progress_args=("Downloading for Catbox...", msg, time.time())
        )
    except Exception as e:
        LOGGER.error(f"Download failed: {e}")
        return await msg.edit(f"Failed to download file: {e}")

    if not file_path:
        return await msg.edit("Failed to download file.")

    await msg.edit("Uploading to Catbox...")

    download_link = await upload_catbox(file_path)

    if not download_link or not download_link.startswith("http"):
        await msg.edit("Catbox failed. Trying Envs.sh...")
        download_link = await upload_envs(file_path)

    if not download_link or not download_link.startswith("http"):
        await msg.edit("Envs.sh failed. Trying Uguu.se...")
        download_link = await upload_uguu(file_path)

    if os.path.exists(file_path):
        os.remove(file_path)

    if download_link and download_link.startswith("http"):
        await msg.edit(f"✅ **File Uploaded Successfully!**\n\n**Download Link:** {download_link.strip()}")
    else:
        error_msg = download_link if download_link else "Unknown error"
        await msg.edit(f"❌ Failed to upload to Catbox and Envs.sh.\nError: {error_msg}")
