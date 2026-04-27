from helper.utils import auth_filter
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from helper.helper_func import ftext, flbl, is_admin, parse_duration, get_readable_time, force_sub
from datetime import datetime, timedelta
import time
import asyncio

# Dictionary to track flood: {chat_id: {"last_user": user_id, "users": {user_id: {"consecutive": count, "timed_msgs": [timestamps], "messages": [msg_ids]}}}}
FLOOD_TRACKER = {}

@Client.on_message(filters.command("flood") & auth_filter)
@force_sub
async def flood_info(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    settings = await client.mongodb.get_flood_settings(message.chat.id)

    consecutive = settings.get("consecutive", 0)
    timed_count = settings.get("timed_count", 0)
    timed_duration = settings.get("timed_duration", 0)
    action = settings.get("action", "mute")
    action_duration = settings.get("action_duration", 0)
    clear_flood = settings.get("clear_flood", False)

    text = f"<blockquote><b>{ftext('Antiflood Settings')}</b></blockquote>\n\n"
    text += f"• <b>{ftext('Consecutive Messages')}:</b> {consecutive if consecutive > 0 else ftext('Disabled')}\n"
    timed_val = f"{timed_count} {ftext('msgs in')} {timed_duration}s" if timed_count > 0 else ftext("Disabled")
    text += f"• <b>{ftext('Timed Flood')}:</b> {timed_val}\n"
    text += f"• <b>{ftext('Action')}:</b> {action.upper()}\n"
    if action in ["tban", "tmute"] and action_duration > 0:
        text += f"• <b>{ftext('Action Duration')}:</b> {get_readable_time(action_duration)}\n"
    text += f"• <b>{ftext('Clear Flood')}:</b> {'✅' if clear_flood else '❌'}"

    await message.reply(text)

@Client.on_message(filters.command("setflood") & auth_filter)
@force_sub
async def set_flood(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if len(message.command) < 2:
        return await message.reply(ftext("Usage: /setflood <number/off>"))

    val = message.command[1].lower()
    if val in ["off", "no", "0"]:
        await client.mongodb.set_flood_settings(message.chat.id, "consecutive", 0)
        await message.reply(ftext("Consecutive antiflood has been disabled."))
    elif val.isdigit():
        num = int(val)
        await client.mongodb.set_flood_settings(message.chat.id, "consecutive", num)
        await message.reply(ftext(f"Consecutive antiflood set to {num} messages."))
    else:
        await message.reply(ftext("Invalid value. Use a number or 'off'."))

@Client.on_message(filters.command("setfloodtimer") & auth_filter)
@force_sub
async def set_flood_timer(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if len(message.command) < 2:
        return await message.reply(ftext("Usage: /setfloodtimer <count> <duration> or /setfloodtimer off"))

    val = message.command[1].lower()
    if val in ["off", "no"]:
        await client.mongodb.set_flood_settings(message.chat.id, "timed_count", 0)
        await message.reply(ftext("Timed antiflood has been disabled."))
    elif len(message.command) >= 3:
        try:
            count = int(message.command[1])
            duration = parse_duration(message.command[2])
            if duration <= 0:
                return await message.reply(ftext("Invalid duration. Use e.g. 30s, 1m."))

            await client.mongodb.set_flood_settings(message.chat.id, "timed_count", count)
            await client.mongodb.set_flood_settings(message.chat.id, "timed_duration", duration)
            await message.reply(ftext(f"Timed antiflood set to {count} messages in {duration} seconds."))
        except ValueError:
            await message.reply(ftext("Invalid input. Count must be a number."))
    else:
        await message.reply(ftext("Usage: /setfloodtimer <count> <duration> or /setfloodtimer off"))

@Client.on_message(filters.command("floodmode") & auth_filter)
@force_sub
async def set_flood_mode(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if len(message.command) < 2:
        return await message.reply(ftext("Usage: /floodmode <ban/mute/kick/tban/tmute> [duration]"))

    action = message.command[1].lower()
    if action not in ["ban", "mute", "kick", "tban", "tmute"]:
        return await message.reply(ftext("Invalid action. Use: ban, mute, kick, tban, tmute."))

    duration = 0
    if action in ["tban", "tmute"]:
        if len(message.command) < 3:
            return await message.reply(ftext(f"Action {action} requires a duration (e.g. 1h, 3d)."))
        duration = parse_duration(message.command[2])
        if duration <= 0:
            return await message.reply(ftext("Invalid duration."))

    await client.mongodb.set_flood_settings(message.chat.id, "action", action)
    await client.mongodb.set_flood_settings(message.chat.id, "action_duration", duration)

    reply_text = f"Antiflood action set to {action.upper()}"
    if duration > 0:
        reply_text += f" for {get_readable_time(duration)}"
    await message.reply(ftext(reply_text))

@Client.on_message(filters.command("clearflood") & auth_filter)
@force_sub
async def set_clear_flood(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if len(message.command) < 2:
        return await message.reply(ftext("Usage: /clearflood <yes/no/on/off>"))

    val = message.command[1].lower()
    status = val in ["yes", "on", "true"]
    await client.mongodb.set_flood_settings(message.chat.id, "clear_flood", status)
    await message.reply(ftext(f"Clear flood messages: {'Enabled' if status else 'Disabled'}"))

@Client.on_message(filters.group & ~filters.bot & ~filters.service, group=1)
async def flood_detector(client: Client, message: Message):
    if not message.from_user:
        return


    # Skip admins
    if await is_admin(client, message.chat.id, message.from_user.id):
        return

    settings = await client.mongodb.get_flood_settings(message.chat.id)
    consecutive_limit = settings.get("consecutive", 0)
    timed_limit = settings.get("timed_count", 0)
    timed_duration = settings.get("timed_duration", 0)

    if consecutive_limit == 0 and timed_limit == 0:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    now = time.time()

    if chat_id not in FLOOD_TRACKER:
        FLOOD_TRACKER[chat_id] = {"last_user": None, "users": {}}

    chat_tracker = FLOOD_TRACKER[chat_id]

    if user_id not in chat_tracker["users"]:
        chat_tracker["users"][user_id] = {
            "consecutive": 0,
            "timed_msgs": [],
            "messages": []
        }

    user_tracker = chat_tracker["users"][user_id]

    # Check if consecutive streak is broken by another user
    if chat_tracker["last_user"] != user_id:
        user_tracker["consecutive"] = 1
        chat_tracker["last_user"] = user_id
    else:
        user_tracker["consecutive"] += 1

    user_tracker["timed_msgs"].append(now)
    user_tracker["messages"].append(message.id)

    # Prune timed messages and corresponding message IDs
    if timed_limit > 0 or timed_duration > 0:
        # Keep only messages within the duration
        cutoff = now - max(timed_duration, 60) # Keep at least 60s for safety or timed_duration

        # Zip them to prune both lists simultaneously
        valid_indices = [i for i, t in enumerate(user_tracker["timed_msgs"]) if t >= cutoff]
        user_tracker["timed_msgs"] = [user_tracker["timed_msgs"][i] for i in valid_indices]
        user_tracker["messages"] = [user_tracker["messages"][i] for i in valid_indices]

    # Limit the number of messages stored to a reasonable maximum if no timed flood is set
    # to prevent memory leak
    max_msgs = max(consecutive_limit, timed_limit, 100)
    if len(user_tracker["messages"]) > max_msgs:
        user_tracker["messages"] = user_tracker["messages"][-max_msgs:]
        if len(user_tracker["timed_msgs"]) > max_msgs:
            user_tracker["timed_msgs"] = user_tracker["timed_msgs"][-max_msgs:]

    # Check for flood
    triggered = False
    reason = ""

    if consecutive_limit > 0 and user_tracker["consecutive"] >= consecutive_limit:
        triggered = True
        reason = f"Consecutive flood ({consecutive_limit} messages)"

    if not triggered and timed_limit > 0:
        # Count messages within the timed_duration window
        recent_msgs_count = sum(1 for t in user_tracker["timed_msgs"] if now - t <= timed_duration)
        if recent_msgs_count >= timed_limit:
            triggered = True
            reason = f"Timed flood ({timed_limit} messages in {timed_duration}s)"

    if triggered:
        # Action to take
        action = settings.get("action", "mute")
        action_duration = settings.get("action_duration", 0)
        clear_flood = settings.get("clear_flood", False)

        msg_ids_to_delete = user_tracker["messages"].copy()

        # Reset tracker for user
        chat_tracker["users"][user_id] = {
            "consecutive": 0,
            "timed_msgs": [],
            "messages": []
        }

        try:
            if action == "ban":
                await message.chat.ban_member(user_id)
            elif action == "kick":
                await message.chat.ban_member(user_id)
                await message.chat.unban_member(user_id)
            elif action == "mute":
                await message.chat.restrict_member(user_id, ChatPermissions())
            elif action == "tban":
                until_date = datetime.now() + timedelta(seconds=action_duration)
                await message.chat.ban_member(user_id, until_date=until_date)
            elif action == "tmute":
                until_date = datetime.now() + timedelta(seconds=action_duration)
                await message.chat.restrict_member(user_id, ChatPermissions(), until_date=until_date)

            dur_text = f" for {get_readable_time(action_duration)}" if action in ["tban", "tmute"] else ""
            await message.reply(ftext(f"User {message.from_user.first_name} has been {action.upper()}ed due to {reason}{dur_text}."))

            if clear_flood and msg_ids_to_delete:
                # Use bulk delete
                await client.delete_messages(chat_id, msg_ids_to_delete)
        except Exception as e:
            client.LOGGER(__name__, client.name).error(f"Failed to take action on flooder: {e}")
