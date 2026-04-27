import base64
import re
import asyncio
import os
import sys
from functools import wraps
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors import UserNotParticipant, Forbidden, PeerIdInvalid, ChatAdminRequired, FloodWait
from datetime import datetime, timedelta
from pyrogram import errors

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    string = string_bytes.decode("ascii")
    return string

async def get_messages(client, channel_id, message_ids):
    """Fetches messages, falling back to backup DB if necessary."""
    final_messages = {}
    ids_to_fetch = list(message_ids)
    
    try:
        all_raw_msgs = []
        for i in range(0, len(ids_to_fetch), 200):
            batch_ids = ids_to_fetch[i:i+200]
            while True:
                try:
                    msgs = await client.get_messages(chat_id=channel_id, message_ids=batch_ids)
                    all_raw_msgs.extend(msgs)
                    break
                except FloodWait as e:
                    await asyncio.sleep(e.value + 1)

        successful_ids = {msg.id for msg in all_raw_msgs if msg and not msg.empty}
        for msg in all_raw_msgs:
            if msg and not msg.empty:
                final_messages[msg.id] = msg

        failed_ids = set(ids_to_fetch) - successful_ids
        
        backup_group = {} # {backup_channel_id: {backup_msg_id: og_msg_id}}
        for og_id in failed_ids:
            res = await client.mongodb.get_backup_msg_id(channel_id, og_id)
            if not res and getattr(client, "master_mongodb", None):
                res = await client.master_mongodb.get_backup_msg_id(channel_id, og_id)
            if res:
                b_msg_id, b_ch_id = res
                if b_ch_id not in backup_group:
                    backup_group[b_ch_id] = {}
                backup_group[b_ch_id][b_msg_id] = og_id
            
        if backup_group:
            for b_ch_id, msg_map in backup_group.items():
                backup_msg_ids = list(msg_map.keys())
                for i in range(0, len(backup_msg_ids), 200):
                    batch_backup_ids = backup_msg_ids[i:i+200]
                    while True:
                        try:
                            backup_msgs = await client.get_messages(b_ch_id, batch_backup_ids)
                            for b_msg in backup_msgs:
                                if b_msg and b_msg.id in msg_map:
                                    final_messages[msg_map[b_msg.id]] = b_msg
                            break
                        except FloodWait as e:
                            await asyncio.sleep(e.value + 1)
    except Exception as e:
        client.LOGGER(__name__, client.name).error(f"Error in get_messages: {e}")
        
    return [final_messages.get(og_id) for og_id in message_ids if og_id in final_messages]

async def get_message_id(client, message: Message):
    """
    Robustly extracts channel_id and message_id from a message.
    Handles modern forwards, deprecated forwards, and text links.
    """
    chat_id, msg_id = (None, None)

    
    if message.forward_from_chat:
        chat_id = message.forward_from_chat.id
        msg_id = message.forward_from_message_id

    elif getattr(message, 'forward_origin', None) and message.forward_origin.chat:
        chat_id = message.forward_origin.chat.id
        msg_id = message.forward_origin.message_id

    if chat_id and (chat_id == getattr(client, 'dump_channel', None)):
        return chat_id, msg_id

    if message.text:
        pattern = r"https://t.me/(?:c/)?(.*?)/(\d+)"
        matches = re.search(pattern, message.text)
        if matches:
            channel_str = matches.group(1)
            msg_id = int(matches.group(2))
            
            dump_id = getattr(client, 'dump_channel', None)
            if dump_id:
                try:
                    if str(dump_id) == f"-100{channel_str}":
                        return dump_id, msg_id
                    chat = await client.get_chat(dump_id)
                    if chat.username and chat.username.lower() == channel_str.lower():
                        return dump_id, msg_id
                except Exception:
                    pass
    
    return 0, 0


def get_readable_time(seconds: int) -> str:
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

async def is_bot_admin(client, channel_id):
    try:
        bot = await client.get_chat_member(channel_id, "me")
        if bot.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            if bot.privileges:
                required = ["can_invite_users", "can_delete_messages"]
                missing = [r for r in required if not getattr(bot.privileges, r, False)]
                if missing:
                    return False, f"Bot is missing rights: {', '.join(missing)}"
            return True, None
        return False, "Bot is not an admin in the channel."
    except errors.ChatAdminRequired:
        return False, "Bot can't access admin info in this channel."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

async def is_admin(client, chat_id, user_id):
    if user_id in client.admins:
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False

async def check_subscription(client, user_id):
    statuses = {}
    for ch_id, (ch_name, ch_link, req, timer) in client.fsub_dict.items():
        if req and await client.mongodb.is_user_in_channel(ch_id, user_id):
            statuses[ch_id] = ChatMemberStatus.MEMBER
            continue
        try:
            user = await client.get_chat_member(ch_id, user_id)
            statuses[ch_id] = user.status
        except UserNotParticipant:
            statuses[ch_id] = ChatMemberStatus.BANNED
        except (Forbidden, ChatAdminRequired):
            client.LOGGER(__name__, client.name).warning(f"Permission error for {ch_name}.")
            statuses[ch_id] = None
        except Exception as e:
            client.LOGGER(__name__, client.name).warning(f"Error checking {ch_name}: {e}")
            statuses[ch_id] = None
    return statuses

def is_user_subscribed(statuses):
    return all(
        s in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}
        for s in statuses.values() if s is not None
    ) and bool(statuses)

def force_sub(func):
    """Decorator to enforce force subscription with a status message."""
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        if not client.fsub_dict:
            return await func(client, message)

        user_id = message.from_user.id if message.from_user else None
        if not user_id:
            return await func(client, message)

        statuses = await check_subscription(client, user_id)
        if is_user_subscribed(statuses):
            return await func(client, message)
        
        photo = client.messages.get('FSUB_PHOTO', '')
        msg = await message.reply_photo(caption=ftext("<b>ᴡᴀɪᴛ ᴀ ꜱᴇᴄᴏɴᴅ....</b>"), photo=photo, parse_mode=ParseMode.HTML) if photo else await message.reply(ftext("<b>ᴡᴀɪᴛ ᴀ ꜱᴇᴄᴏɴᴅ....</b>"), parse_mode=ParseMode.HTML)
        
        buttons = []
        status_lines = []
        for ch_id, (ch_name, ch_link, req, timer) in client.fsub_dict.items():
            status = statuses.get(ch_id)
            if status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
                status_text = "<b>Joined</b> ✅"
            else:
                status_text = "<i>Required</i> ❗️"
                if timer > 0:
                    invite = await client.create_chat_invite_link(chat_id=ch_id, expire_date=datetime.now() + timedelta(minutes=timer), creates_join_request=req)
                    ch_link = invite.invite_link
                buttons.append(InlineKeyboardButton(flbl(f"Join {ch_name}"), url=ch_link))
            status_lines.append(ftext(f"› {ch_name} - {status_text}"))
        
        fsub_text = client.messages.get('FSUB', "<blockquote><b>Join Required</b></blockquote>\nYou must join the following channel(s) to continue:")
        channels_message = ftext(f"{fsub_text}\n\n") + "\n".join(status_lines)

        try_again_button = []
        if len(message.text.split()) > 1:
            try:
                try_again_link = f"https://t.me/{client.username}/?start={message.text.split()[1]}"
                try_again_button = [InlineKeyboardButton(flbl("Try Again"), url=try_again_link)]
            except Exception:
                pass

        button_layout = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        if try_again_button:
            button_layout.append(try_again_button)
        
        try:
            await msg.edit(text=channels_message, reply_markup=InlineKeyboardMarkup(button_layout) if button_layout else None, parse_mode=ParseMode.HTML)
        except Exception as e:
            client.LOGGER(__name__, client.name).warning(f"Error updating FSUB message: {e}")
        message.stop_propagation()
    return wrapper


def font_shaper(text: str) -> str:
    """
    Converts alphanumeric characters to Mathematical Sans-Serif style ('wards'),
    while preserving HTML tags, mentions, and URLs.
    """
    if not text:
        return text

    def replace_char(char):
        if 'A' <= char <= 'Z':
            return chr(ord(char) - ord('A') + 0x1D5A0)
        elif 'a' <= char <= 'z':
            return chr(ord(char) - ord('a') + 0x1D5BA)
        elif '0' <= char <= '9':
            # Mathematical Sans-Serif Digits (𝟢-𝟫)
            # 0 -> 0x1D7E2, 1 -> 0x1D7E3, ..., 4 -> 0x1D7E6, ...
            return chr(ord(char) - ord('0') + 0x1D7E2)
        return char

    # Regex to identify HTML tags, Telegram mentions, and URLs
    pattern = r'(<[^>]+>|@[A-Za-z0-9_]+|https?://[^\s<>"]+|www\.[^\s<>"]+)'

    # Split text into parts (content and excluded patterns)
    parts = re.split(pattern, text)

    result = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # This is normal text, apply font shaping
            result.append("".join(replace_char(c) for c in part))
        else:
            # This matches the pattern, preserve it
            result.append(part)

    return "".join(result)

def ftext(text: str) -> str:
    """Alias for font_shaper to be used for message bodies."""
    return font_shaper(text)

def parse_duration(duration_str: str) -> int:
    """
    Parses a duration string (e.g., '30s', '1m', '1h', '1d') into seconds.
    """
    if not duration_str:
        return 0

    duration_str = duration_str.lower().strip()
    match = re.match(r"^(\d+)([smhd])$", duration_str)
    if not match:
        try:
            return int(duration_str)
        except ValueError:
            return 0

    value, unit = match.groups()
    value = int(value)

    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    elif unit == 'd':
        return value * 86400

    return 0

def flbl(text: str) -> str:
    """For button labels, prepending '✦ ' and applying font_shaper."""
    if not text:
        return text
    # Avoid double prepending
    if not text.startswith("✦"):
        text = f"✦ {text}"
    return font_shaper(text)

def convert_bytes(size):
    """Converts bytes into a human-readable string."""
    if size is None: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f %s" % (size, unit)
        size /= 1024.0
    return "0 B"

def truncate_html(text: str, max_length: int = 4000) -> str:
    """
    Safely truncates HTML-formatted text to a maximum length while ensuring tags are closed.
    """
    if not text or len(text) <= max_length:
        return text

    # Truncate at max_length
    truncated = text[:max_length]

    # If we are inside a tag, back up to before the tag started
    last_open = truncated.rfind('<')
    last_close = truncated.rfind('>')

    if last_open > last_close:
        truncated = truncated[:last_open]

    # Find all start and end tags
    # This regex is simplified but works for common Telegram HTML tags (b, i, u, s, code, pre, a, blockquote)
    start_tags = re.findall(r'<(b|i|u|s|code|pre|a|blockquote|spoiler|emoji)(?:\s+[^>]*)?>', truncated, re.IGNORECASE)
    end_tags = re.findall(r'</(b|i|u|s|code|pre|a|blockquote|spoiler|emoji)>', truncated, re.IGNORECASE)

    # Simple stack to find unclosed tags
    stack = []
    # We need to process tags in order to accurately determine which are open.
    # A simple re.findall doesn't give us the order of start/end tags.

    all_tags = re.findall(r'<(/?)(b|i|u|s|code|pre|a|blockquote|spoiler|emoji)(?:\s+[^>]*)?>', truncated, re.IGNORECASE)

    for is_end, tag_name in all_tags:
        tag_name = tag_name.lower()
        if is_end:
            if stack and stack[-1] == tag_name:
                stack.pop()
        else:
            stack.append(tag_name)

    # Append closing tags in reverse order
    for tag in reversed(stack):
        truncated += f"</{tag}>"

    return truncated

async def graceful_restart(client, update):
    """Waits for background tasks before restarting."""
    from bot import Bot

    # Identify all background tasks across all bot instances
    all_tasks = []
    for bot in Bot._bot_instances:
        all_tasks.extend(list(bot.background_tasks))

    if all_tasks:
        msg_text = f"⏳ **Restarting...**\nWaiting for {len(all_tasks)} background tasks to complete."
        if isinstance(update, Message):
            status_msg = await update.reply_text(ftext(msg_text))
        else:
            await update.answer(ftext("Restarting... Waiting for tasks."), show_alert=True)
            status_msg = await update.message.edit_text(ftext(msg_text))

        # Wait for tasks with a timeout of 30 seconds
        try:
            await asyncio.wait(all_tasks, timeout=30)
        except Exception:
            pass

        await status_msg.edit_text(ftext("🔄 **Restarting now...**"))
    else:
        if isinstance(update, Message):
            await update.reply_text(ftext("🔄 **Restarting...**"))
        else:
            await update.answer(ftext("Restarting..."), show_alert=True)
            await update.message.edit_text(ftext("🔄 **Restarting...**"))

    # Execute restart
    os.execl(sys.executable, sys.executable, *sys.argv)
