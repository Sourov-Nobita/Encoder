from helper.utils import auth_filter
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaDocument, Message, InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image
from datetime import datetime
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, humanbytes, convert, add_task, start_task, remove_task, semaphore, download_semaphore, upload_semaphore, auth_filter, auth_user
from helper.helper_func import ftext, flbl
from helper.anime_utils import get_thumbnail
from helper.ffmpeg import fix_video
from config import Var
import os
import time
import re
import asyncio
import shutil
import aiohttp
import random
import string

def sanitize_filename(filename):
    # Remove invalid characters and trailing dots/spaces
    filename = re.sub(r'[\/*?:"<>|]', '', filename)
    return filename.strip().strip('.')

def clean_filename(filename):
    # Remove the telegram prefix if it exists (e.g. 8584729307_1773321117_BQACAgQA_)
    filename = re.sub(r'^\d+_\d+_[A-Za-z0-9]+_', '', filename)
    # Replace underscores with spaces
    filename = filename.replace('_', ' ')
    # Remove extra spaces
    filename = ' '.join(filename.split())
    return filename

# Pattern 1: S01E02 or S01EP02 or S01_E01
pattern1 = re.compile(r'S(\d+)[._\s-]*(?:E|EP)(\d+)', re.IGNORECASE)
# Pattern 2: S01 E02 or S01 EP02 or S01 - E01 or S01 - EP02 or S01_01
pattern2 = re.compile(r'S(\d+)[._\s-]*(\d+)', re.IGNORECASE)
# Pattern 3: Episode Number After "E" or "EP"
pattern3 = re.compile(r'(?:[([<{]?\s*(?:E|EP)[._\s-]*(\d+)\s*[)\]>}]?)', re.IGNORECASE)
# Pattern 3_2: episode number after - [hyphen]
pattern3_2 = re.compile(r'(?:\s*-\s*(\d+)\s*)')
# Pattern 4: S2 09 ex.
pattern4 = re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)
# Pattern X: Standalone Episode Number
patternX = re.compile(r'(\d+)')
#QUALITY PATTERNS 
# Pattern 5: 3-4 digits followed by 'p' as quality
pattern5 = re.compile(r'(\d{3,4}p)', re.IGNORECASE)
# Pattern 6: Find 4k in brackets or parentheses
pattern6 = re.compile(r'[([<{]?\s*4k\s*[)\]>}]?', re.IGNORECASE)
# Pattern 7: Find 2k in brackets or parentheses
pattern7 = re.compile(r'[([<{]?\s*2k\s*[)\]>}]?', re.IGNORECASE)
# Pattern 8: Find HdRip without spaces
pattern8 = re.compile(r'[([<{]?\s*HdRip\s*[)\]>}]?|\bHdRip\b', re.IGNORECASE)
# Pattern 9: Find 4kX264 in brackets or parentheses
pattern9 = re.compile(r'[([<{]?\s*4kX264\s*[)\]>}]?', re.IGNORECASE)
# Pattern 10: Find 4kx265 in brackets or parentheses
pattern10 = re.compile(r'[([<{]?\s*4kx265\s*[)\]>}]?', re.IGNORECASE)

# SEASON PATTERNS
# Pattern 11: S01 or S 01 or Season 01
pattern11 = re.compile(r'S(?:eason)?[._\s-]*(\d+)', re.IGNORECASE)

# AUDIO PATTERNS
# Pattern 12: Dual Audio, Multi Audio, Hindi, English etc.
pattern12 = re.compile(r'[([<{]?\s*(Dual Audio|Multi Audio|Hindi|English|Tamil|Telugu|Malayalam|Kannada|Bengali|Gujarati|Punjabi|Marathi)\s*[)\]>}]?', re.IGNORECASE)

# MANGA PATTERNS
# Pattern 13: Volume Number (V01, Vol 01, Volume 01)
pattern13 = re.compile(r'V(?:ol(?:ume)?)?[._\s-]*(\d+)', re.IGNORECASE)
# Pattern 14: Chapter Number (C01, Ch 01, Chapter 01)
pattern14 = re.compile(r'C(?:h(?:apter)?)?[._\s-]*(\d+)', re.IGNORECASE)

def extract_season(filename):
    match = re.search(pattern11, filename)
    if match:
        return match.group(1)
    return ""

def extract_audio(filename):
    match = re.search(pattern12, filename)
    if match:
        return match.group(1)
    return ""

def extract_volume(filename):
    match = re.search(pattern13, filename)
    if match:
        return match.group(1)
    return ""

def extract_chapter(filename):
    match = re.search(pattern14, filename)
    if match:
        return match.group(1)
    return ""

def extract_quality(filename):
    # Try Quality Patterns
    match5 = re.search(pattern5, filename)
    if match5:
        return match5.group(1)

    match6 = re.search(pattern6, filename)
    if match6:
        return "4k"

    match7 = re.search(pattern7, filename)
    if match7:
        return "2k"

    match8 = re.search(pattern8, filename)
    if match8:
        return "HdRip"

    match9 = re.search(pattern9, filename)
    if match9:
        return "4kX264"

    match10 = re.search(pattern10, filename)
    if match10:
        return "4kx265"

    return ""
    

def extract_episode_number(filename):    
    # Prioritize explicit episode markers
    match = re.search(pattern3, filename)
    if match: return match.group(1)

    match = re.search(pattern1, filename)
    if match: return match.group(2)
    
    match = re.search(pattern2, filename)
    if match: return match.group(2)

    match = re.search(pattern3_2, filename)
    if match: return match.group(1)
        
    match = re.search(pattern4, filename)
    if match: return match.group(2)

    # Standalone numbers with filtering
    matches = re.findall(r'(\d+)', filename)
    for num in matches:
        if 1900 <= int(num) <= 2100: # Likely a year
            continue
        if num in ['480', '720', '1080', '2160']: # Likely resolution
            # Check if it's followed by 'p' or preceded by 'x'
            idx = filename.find(num)
            if idx + len(num) < len(filename) and filename[idx + len(num)].lower() == 'p':
                continue
            if idx > 0 and filename[idx-1].lower() == 'x':
                continue
        return num
        
    return None

@Client.on_message(filters.command("autorename") & auth_filter)
async def set_format(client, message):
    if not await auth_user(None, client, message):
        return await message.reply(ftext(client.reply_text))
    if len(message.command) == 1:
        return await message.reply_text(ftext("Please provide a format template.\nExample: `/autorename {filename} {quality} {episode}`"))

    template = message.text.split(None, 1)[1]
    await client.mongodb.set_format_template(message.from_user.id, template)
    await message.reply_text(ftext(f"✅ **Auto Rename Format Set Successfully!**\n\n**Format:** `{template}`"))

@Client.on_message(filters.command("show_format") & auth_filter)
async def show_format(client, message):
    if not await auth_user(None, client, message):
        return await message.reply(ftext(client.reply_text))
    template = await client.mongodb.get_format_template(message.from_user.id)
    if not template:
        return await message.reply_text(ftext("No Auto Rename format set yet."))
    await message.reply_text(ftext(f"**Current Auto Rename Format:**\n\n`{template}`"))

async def process_file(client, message, user_id, custom_name=None, custom_type=None):
    if not custom_name:
        format_template = await client.mongodb.get_format_template(user_id)
        if not format_template:
            return await message.reply_text(ftext("Please Set An Auto Rename Format First"))

    media_preference = await client.mongodb.get_media_preference(user_id)

    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
        media_type = custom_type or media_preference or "document"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name if message.video.file_name else "video.mp4"
        media_type = custom_type or media_preference or "video"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = f"{message.audio.file_name}.mp3" if message.audio.file_name else "audio.mp3"
        media_type = custom_type or media_preference or "audio"
    else:
        return await message.reply_text(ftext("Unsupported File Type"))

    # Anti-flood / duplicate check
    if file_id in client.renaming_operations:
        elapsed_time = (datetime.now() - client.renaming_operations[file_id]).seconds
        if elapsed_time < 10:
            return
    client.renaming_operations[file_id] = datetime.now()

    # Add task to queue
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    task_id = f"{user_id}_{int(time.time())}_{random_str}"
    add_task(user_id, task_id, client=client)

    async with semaphore:
        start_task(task_id)
        # Use absolute path for robustness
        task_dir = os.path.abspath(f"downloads/{task_id}") + "/"
        os.makedirs(task_dir, exist_ok=True)

        file_path = None
        original_file = None
        download_msg = None

        try:
            # Clean filename first
            cleaned_file_name = clean_filename(file_name)
            base_name, file_extension = os.path.splitext(cleaned_file_name)

            # Get user's preferred rename source
            rename_source = await client.mongodb.get_rename_source(user_id)

            if rename_source == "caption" and message.caption:
                source_for_meta = message.caption
            else:
                source_for_meta = cleaned_file_name

            episode_number = extract_episode_number(source_for_meta)
            extracted_qualities = extract_quality(source_for_meta)
            season_number = extract_season(source_for_meta)
            audio_language = extract_audio(source_for_meta)
            volume_number = extract_volume(source_for_meta)
            chapter_number = extract_chapter(source_for_meta)

            # Extra placeholders
            file_size_formatted = humanbytes(getattr(message.document or message.video or message.audio, "file_size", 0))
            video_duration = getattr(message.video or message.audio, "duration", 0)
            video_duration_formatted = convert(video_duration)
            current_date = datetime.now().strftime("%d-%m-%Y")

            # Fallback if metadata not found in preferred source
            if not episode_number:
                fallback_source = cleaned_file_name if rename_source == "caption" else (message.caption if message.caption else cleaned_file_name)
                episode_number = extract_episode_number(fallback_source)
            if not extracted_qualities:
                fallback_source = cleaned_file_name if rename_source == "caption" else (message.caption if message.caption else cleaned_file_name)
                extracted_qualities = extract_quality(fallback_source)
            if not season_number:
                fallback_source = cleaned_file_name if rename_source == "caption" else (message.caption if message.caption else cleaned_file_name)
                season_number = extract_season(fallback_source)
            if not audio_language:
                fallback_source = cleaned_file_name if rename_source == "caption" else (message.caption if message.caption else cleaned_file_name)
                audio_language = extract_audio(fallback_source)
            if not volume_number:
                fallback_source = cleaned_file_name if rename_source == "caption" else (message.caption if message.caption else cleaned_file_name)
                volume_number = extract_volume(fallback_source)
            if not chapter_number:
                fallback_source = cleaned_file_name if rename_source == "caption" else (message.caption if message.caption else cleaned_file_name)
                chapter_number = extract_chapter(fallback_source)

            # Always apply the format template or use custom name
            if custom_name:
                new_file_name = sanitize_filename(custom_name)
                caption_filename = new_file_name
            else:
                use_default = False
                if "{default}" in format_template.lower():
                    use_default = True
                    format_template = re.sub(r'\{default\}', '', format_template, flags=re.IGNORECASE)

                # Replace placeholders with actual values
                format_template = re.sub(r'\{?episode\}?', str(episode_number or ""), format_template, flags=re.IGNORECASE)
                format_template = re.sub(r'\{?quality\}?', str(extracted_qualities or ""), format_template, flags=re.IGNORECASE)
                format_template = re.sub(r'\{?filename\}?', str(base_name or ""), format_template, flags=re.IGNORECASE)
                format_template = re.sub(r'\{?season\}?', str(season_number or ""), format_template, flags=re.IGNORECASE)
                format_template = re.sub(r'\{?audio\}?', str(audio_language or ""), format_template, flags=re.IGNORECASE)
                format_template = re.sub(r'\{?volume\}?', str(volume_number or ""), format_template, flags=re.IGNORECASE)
                format_template = re.sub(r'\{?chapter\}?', str(chapter_number or ""), format_template, flags=re.IGNORECASE)
                format_template = re.sub(r'\{?filesize\}?', str(file_size_formatted or ""), format_template, flags=re.IGNORECASE)
                format_template = re.sub(r'\{?duration\}?', str(video_duration_formatted or ""), format_template, flags=re.IGNORECASE)
                format_template = re.sub(r'\{?date\}?', str(current_date or ""), format_template, flags=re.IGNORECASE)

                if use_default:
                    new_file_name = "noname" + file_extension
                    # For caption, if template is effectively empty, use noname too
                    if not format_template.strip():
                        caption_filename = "noname" + file_extension
                    else:
                        caption_filename = sanitize_filename(f"{format_template}{file_extension}")
                        if not caption_filename: # In case sanitize_filename stripped everything
                             caption_filename = "noname" + file_extension
                else:
                    new_file_name = sanitize_filename(f"{format_template}{file_extension}")
                    caption_filename = new_file_name

            new_file_name = ' '.join(new_file_name.split()) # Remove extra spaces
            caption_filename = ' '.join(caption_filename.split())
            file_path = task_dir + new_file_name

            download_msg = await message.reply_text(text="Trying To Download.....")

            async with download_semaphore:
                try:
                    while True:
                        try:
                            path = await client.download_media(message=message, file_name=file_path, progress=progress_for_pyrogram, progress_args=("Download Started....", download_msg, time.time()))
                            break
                        except FloodWait as e:
                            await asyncio.sleep(e.value + 1)
                except Exception as e:
                    return await download_msg.edit(str(e))

            # Extract metadata before possible re-encoding
            duration = 0
            width = 0
            height = 0
            try:
                metadata_info = extractMetadata(createParser(file_path))
                if metadata_info.has("duration"):
                    duration = metadata_info.get('duration').seconds
                if metadata_info.has("width"):
                    width = metadata_info.get("width")
                    if width % 2 != 0: width -= 1
                if metadata_info.has("height"):
                    height = metadata_info.get("height")
                    if height % 2 != 0: height -= 1
            except:
                pass

            watermark_url = await client.mongodb.get_watermark_url(user_id)
            watermark_status = await client.mongodb.get_watermark_status(user_id)
            metadata_status = await client.mongodb.get_metadata_status(user_id)
            metadata = await client.mongodb.get_metadata(user_id)

            if (watermark_url and watermark_status and width > 0) or metadata_status:
                try:
                    await download_msg.edit(f"Processing Media...")
                    success, error = await fix_video(client, download_msg, file_path, task_dir, user_id, new_file_name, width, height, duration, watermark_url, watermark_status, metadata_status, metadata)
                    if not success:
                        print(f"FFMPEG Error: {error}")
                except Exception as e:
                    print(f"FFMPEG Error: {e}")

            upload_msg = await download_msg.edit(f"Trying To Uploading.....")
            c_caption = await client.mongodb.get_caption(user_id)
            caption = c_caption.format(filename=f"**{caption_filename}**", filesize=humanbytes(os.path.getsize(file_path)), duration=convert(duration)) if c_caption else f"**{caption_filename}**"

            ph_path = await get_thumbnail(client, user_id, message, task_dir)

            # Determine upload destination
            upload_mode = await client.mongodb.get_upload_mode(user_id)
            if upload_mode == "pm":
                destination = user_id
            elif upload_mode == "channel":
                destination = await client.mongodb.get_upload_channel(user_id) or message.chat.id
            else:
                destination = message.chat.id

            async with upload_semaphore:
                fille = None
                try:
                    if not os.path.exists(file_path):
                        return await upload_msg.edit("File Not Found! Maybe it was deleted during processing.")

                    while True:
                        try:
                            upload_to = destination
                            if upload_mode == "channel" and not (await client.mongodb.get_upload_channel(user_id)):
                                upload_to = getattr(client, "dump_channel", None) or destination

                            if media_type == "document":
                                fille = await client.send_document(
                                    upload_to,
                                    document=file_path,
                                    thumb=ph_path,
                                    caption=caption,
                                    progress=progress_for_pyrogram,
                                    progress_args=(f"Upload Started.....", upload_msg, time.time())
                                )
                            elif media_type == "video":
                                fille = await client.send_video(
                                    upload_to,
                                    video=file_path,
                                    caption=caption,
                                    thumb=ph_path,
                                    width=width,
                                    height=height,
                                    duration=duration,
                                    progress=progress_for_pyrogram,
                                    progress_args=(f"Upload Started.....", upload_msg, time.time())
                                )
                            elif media_type == "audio":
                                fille = await client.send_audio(
                                    upload_to,
                                    audio=file_path,
                                    caption=caption,
                                    thumb=ph_path,
                                    duration=duration,
                                    progress=progress_for_pyrogram,
                                    progress_args=(f"Upload Started.....", upload_msg, time.time())
                                )
                            break
                        except FloodWait as e:
                            await asyncio.sleep(e.value + 1)

                    # Copy to dump if not already uploaded there
                    dump_channel = getattr(client, "dump_channel", None)
                    if dump_channel and upload_to != dump_channel:
                        if fille and not fille.empty:
                            try: await fille.copy(dump_channel)
                            except: pass

                    await upload_msg.edit(f"✅ Uploaded Successfully!")
                except Exception as e:
                    await upload_msg.edit(f"Error: {e}")
                finally:
                    pass

            if download_msg: await download_msg.delete()

        finally:
            shutil.rmtree(task_dir, ignore_errors=True)
            if file_id in client.renaming_operations:
                del client.renaming_operations[file_id]
            remove_task(user_id, task_id, client=client)
