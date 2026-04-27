import asyncio
import aiohttp
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup
from pyrogram.errors import FloodWait, MessageTooLong
import re
import os
import logging
from PIL import Image
from helper.helper_func import convert_bytes, font_shaper, truncate_html

LOGGER = logging.getLogger(__name__)

_session = None

async def get_session():
    global _session
    if _session is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        _session = aiohttp.ClientSession(headers=headers)
    return _session


def convertBytes(size):
    return convert_bytes(size)

def convertTime(seconds: int) -> str:
    if seconds is None: return "0s"
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0: break
        time_list.append(int(result))
        seconds = int(remainder)
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

async def sendMessage(client: Client, chat_id, text, reply_markup=None):
    while True:
        try:
            return await client.send_message(chat_id, text, reply_markup=reply_markup)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
        except MessageTooLong:
            text = truncate_html(text)
        except Exception as e:
            LOGGER.error(f"Error in sendMessage: {e}")
            return str(e)

async def editMessage(message: Message, text, reply_markup=None):
    while True:
        try:
            return await message.edit_text(text, reply_markup=reply_markup)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
        except MessageTooLong:
            text = truncate_html(text)
        except Exception as e:
            # LOGGER.error(f"Error in editMessage: {e}")
            return str(e)

def sans_fonts(text: str) -> str:
    return font_shaper(text)

async def get_thumbnail(client, user_id, media_msg, task_dir):
    """
    Resolves and prepares a thumbnail for a given user and media message.
    Priority: User-specific (DB) > Media-specific (Original) > Global Bot-specific.
    """
    ph_path = None
    c_thumb = await client.mongodb.get_thumbnail(user_id)

    try:
        if c_thumb:
            if isinstance(c_thumb, str) and (c_thumb.startswith("http://") or c_thumb.startswith("https://")):
                # Download URL thumbnail
                session = await get_session()
                async with session.get(c_thumb) as resp:
                    if resp.status == 200:
                        ph_path = os.path.join(task_dir, "thumb_user.jpg")
                        with open(ph_path, "wb") as f:
                            f.write(await resp.read())
            else:
                # Download FileID thumbnail
                while True:
                    try:
                        ph_path = await client.download_media(c_thumb, file_name=os.path.join(task_dir, "thumb_user.jpg"))
                        break
                    except FloodWait as e:
                        await asyncio.sleep(e.value + 1)

        if not ph_path and media_msg:
            media = getattr(media_msg, media_msg.media.value if media_msg.media else "", None)
            if media and hasattr(media, "thumbs") and media.thumbs:
                while True:
                    try:
                        ph_path = await client.download_media(media.thumbs[0].file_id, file_name=os.path.join(task_dir, "thumb_media.jpg"))
                        break
                    except FloodWait as e:
                        await asyncio.sleep(e.value + 1)

        if not ph_path and client.thumbnail:
            if os.path.exists(client.thumb_path):
                ph_path = os.path.join(task_dir, "thumb_global.jpg")
                import shutil
                shutil.copy(client.thumb_path, ph_path)

        if ph_path:
            try:
                img = Image.open(ph_path).convert("RGB")
                img.thumbnail((320, 320))
                img.save(ph_path, "JPEG")
                return ph_path
            except Exception as e:
                LOGGER.error(f"Error processing thumbnail: {e}")
                return None
    except Exception as e:
        LOGGER.error(f"Error resolving thumbnail: {e}")
        return None

    return None

async def mediainfo(path, get_duration=False):
    import json
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", path
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        return 0.0 if get_duration else None
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return 0.0 if get_duration else None

    if get_duration:
        try:
            return float(data.get('format', {}).get('duration', 0))
        except (ValueError, TypeError):
            return 0.0
    return data

def handle_logs(func):
    from functools import wraps
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            LOGGER.error(f"Error in {func.__name__}: {e}")
            raise e
    return wrapper
