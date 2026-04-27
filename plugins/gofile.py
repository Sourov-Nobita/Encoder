from helper.utils import auth_filter, auth_user, progress_for_pyrogram
from helper.helper_func import ftext
import aiohttp
import os
import logging

LOGGER = logging.getLogger(__name__)

async def get_server():
    """Get the available gofile server for upload."""
    # Preferred endpoint
    url = "https://api.gofile.io/getServer"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "ok":
                        return data.get("data", {}).get("server")
    except Exception as e:
        LOGGER.debug(f"Error getting gofile server via getServer: {e}")

    # Fallback to servers list
    url = "https://api.gofile.io/servers"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "ok":
                        servers = data.get("data", {}).get("servers", [])
                        if servers:
                            return servers[0].get("name")
    except Exception as e:
        LOGGER.error(f"Error getting gofile server via servers list: {e}")
    return None

async def upload_gofile(file_path, token=None):
    """Upload a file to gofile.io."""
    server = await get_server()
    if not server:
        LOGGER.error("Could not get gofile server.")
        return None

    # Modern upload endpoint
    url = f"https://{server}.gofile.io/uploadFile"
    file_name = os.path.basename(file_path)

    try:
        # We use a context manager for the file to ensure it's closed correctly
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            # Adding filename explicitly improves reliability
            data.add_field('file', f, filename=file_name)
            if token:
                data.add_field('token', token)

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("status") == "ok":
                            return result.get("data", {}).get("downloadPage")
                        else:
                            LOGGER.error(f"Gofile upload error for {file_name}: {result}")
                    else:
                        text = await response.text()
                        LOGGER.error(f"Gofile upload failed for {file_name} with status {response.status}: {text}")
    except Exception as e:
        LOGGER.error(f"Error in gofile upload for {file_name}: {e}")
    return None

from pyrogram import Client, filters
import time

@Client.on_message(filters.command("gofile") & auth_filter)
async def gofile_upload_handler(client, message):
    if not await auth_user(None, client, message):
        return await message.reply(ftext(client.reply_text))
    reply = message.reply_to_message
    if not reply or not (reply.document or reply.video or reply.audio):
        return await message.reply_text("Please reply to a file/video/audio to upload it to GoFile.")

    user_id = message.from_user.id
    token = await client.mongodb.get_gofile_token(user_id)

    msg = await message.reply_text("Downloading file to upload to GoFile...")

    file_path = await client.download_media(
        reply,
        progress=progress_for_pyrogram,
        progress_args=("Downloading for GoFile...", msg, time.time())
    )

    if not file_path:
        return await msg.edit("Failed to download file.")

    await msg.edit("Uploading to GoFile...")

    download_link = await upload_gofile(file_path, token=token)

    if os.path.exists(file_path):
        os.remove(file_path)

    if download_link:
        await msg.edit(f"✅ **File Uploaded Successfully!**\n\n**Download Link:** {download_link}")
    else:
        await msg.edit("❌ Failed to upload to GoFile.")
