import math
import time
import asyncio
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatType
from config import Var
import os

def is_video(message: Message) -> bool:
    """Checks if a message contains a video or a video document."""
    if not message:
        return False
    if message.video:
        return True
    if message.document and message.document.mime_type:
        if message.document.mime_type.startswith("video/"):
            return True
        # Extra check for MKV and other common video extensions if mime-type is generic
        filename = message.document.file_name or ""
        if filename.lower().endswith((".mkv", ".mp4", ".webm", ".avi", ".mov", ".flv", ".wmv")):
            return True
    return False

# Semaphores to limit concurrent tasks
semaphore = asyncio.Semaphore(1)
download_semaphore = asyncio.Semaphore(1)
upload_semaphore = asyncio.Semaphore(1)

def add_task(user_id, task_id, client):
    tasks = client.user_tasks
    if user_id not in tasks:
        tasks[user_id] = []
    tasks[user_id].append(task_id)

def start_task(task_id):
    # This can be used for logging or more detailed tracking
    pass

def remove_task(user_id, task_id, client):
    tasks = client.user_tasks
    if user_id in tasks and task_id in tasks[user_id]:
        tasks[user_id].remove(task_id)

def humanbytes(size):
    if not size:
        return "0 B"
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        elapsed_time = round(diff)
        eta = round((total - current) / speed) if speed > 0 else 0

        # We use sans_fonts and other helpers if available, but utils.py is low-level
        # Let's use simple but clean formatting here.
        bar_size = 20
        filled = int(percentage / (100 / bar_size))
        bar = '█' * filled + '░' * (bar_size - filled)

        # Import helper_func here to avoid circular imports
        from helper.helper_func import font_shaper

        status_text = font_shaper(f"{ud_type}...")

        tmp = f"""<blockquote>‣ <b>{font_shaper('Status')} :</b> <i>{status_text}</i>
<code>[{bar}]</code> {percentage:.2f}% </blockquote>

<blockquote>‣ <b>{font_shaper('Size')} :</b> {humanbytes(current)} {font_shaper('out of')} ~ {humanbytes(total)}
‣ <b>{font_shaper('Speed')} :</b> {humanbytes(speed)}/s
‣ <b>{font_shaper('Time Took')} :</b> {TimeFormatter(elapsed_time * 1000)}
‣ <b>{font_shaper('Time Left')} :</b> {TimeFormatter(eta * 1000)} </blockquote>"""

        try:
            await message.edit(text=tmp)
        except Exception:
            pass

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

async def auth_user(filters, client, message: Message):
    # If it's an authorized group, allow everyone (including anonymous admins)
    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        if await client.mongodb.is_group_authorized(message.chat.id):
            return True

    if not message.from_user:
        return False

    if message.from_user.id in client.admins:
        return True

    return False

auth_filter = filters.create(auth_user)
