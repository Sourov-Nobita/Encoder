from helper.utils import auth_filter
from helper.helper_func import ftext, flbl
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.enums import ParseMode
from config import MSG_EFFECT


async def send_start_message(client: Client, message_or_query):
    """
    A single, robust function to send the start message.
    Handles both /start command (Message) and Home button (CallbackQuery)
    and correctly manages transitions between photo and text messages.
    """
    is_callback = isinstance(message_or_query, CallbackQuery)
    
    if is_callback:
        message = message_or_query.message
        user = message_or_query.from_user
        await message_or_query.answer()
    else:
        message = message_or_query
        user = message_or_query.from_user

    start_photo = client.messages.get('START_PHOTO', '')
    start_text_template = client.messages.get('START', 'No Start Message')
    
    buttons = [[InlineKeyboardButton(flbl("About"), callback_data="about"), InlineKeyboardButton(flbl("Close"), callback_data="close")]]
    if user.id in client.admins :
        buttons.insert(0, [InlineKeyboardButton(flbl("Settings"), callback_data="settings")])

    start_text = ftext(start_text_template.format(
        first=user.first_name,
        last=user.last_name or "",
        username=f'@{user.username}' if user.username else 'None',
        mention=user.mention,
        id=user.id
    ))
    
    reply_markup = InlineKeyboardMarkup(buttons)

    if start_photo:
        if is_callback and message.photo:
            await message.edit_media(media=InputMediaPhoto(media=start_photo, caption=start_text), reply_markup=reply_markup)
        else:
            if is_callback: await message.delete()
            await client.send_photo(chat_id=message.chat.id, photo=start_photo, caption=start_text, reply_markup=reply_markup)
    else:
        if is_callback and not message.photo:
            await message.edit_text(text=start_text, reply_markup=reply_markup)
        else:
            if is_callback: await message.delete()
            await client.send_message(chat_id=message.chat.id, text=start_text, reply_markup=reply_markup)


@Client.on_callback_query(filters.regex('^home$'))
async def home(client: Client, query: CallbackQuery):
    """Handles the 'Home' button by calling the master start message function."""
    await send_start_message(client, query)

@Client.on_callback_query(filters.regex('^about$'))
async def about(client: Client, query: CallbackQuery):
    await query.answer()
    
    buttons = [[InlineKeyboardButton(flbl("Home"), callback_data="home"), InlineKeyboardButton(flbl("Close"), callback_data="close")]]
    
    about_text = ftext(client.messages.get('ABOUT', 'No About Message').format(
        owner_id=client.owner,
        bot_username=client.username,
        first=query.from_user.first_name,
        last=query.from_user.last_name or "",
        username=f'@{query.from_user.username}' if query.from_user.username else 'None',
        mention=query.from_user.mention,
        id=query.from_user.id
    ))
    
    about_photo = client.messages.get('ABOUT_PHOTO', '')
    
    if about_photo:
        if query.message.photo:
            await query.message.edit_media(media=InputMediaPhoto(media=about_photo, caption=about_text), reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await query.message.delete()
            await client.send_photo(chat_id=query.message.chat.id, photo=about_photo, caption=about_text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        if query.message.photo:
            await query.message.delete()
            await client.send_message(query.message.chat.id, about_text, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await query.message.edit_text(text=about_text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_message(filters.command('ban') & auth_filter)
async def ban(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))
    if len(message.command) < 2:
        return await message.reply(ftext("<b>Usage:</b> /ban <user_id1> <user_id2> ..."))
    try:
        user_ids = message.text.split(maxsplit=1)[1]
        c = 0
        for user_id_str in user_ids.split():
            user_id = int(user_id_str)
            c += 1
            if user_id in client.admins: continue
            if not await client.mongodb.present_user(user_id):
                await client.mongodb.add_user(user_id, True)
            else:
                await client.mongodb.ban_user(user_id)
        return await message.reply(ftext(f"{c} users have been banned!"))
    except Exception as e:
        return await message.reply(ftext(f"**Error:** {e}"))

@Client.on_message(filters.command('unban') & auth_filter)
async def unban(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))
    if len(message.command) < 2:
        return await message.reply(ftext("<b>Usage:</b> /unban <user_id1> <user_id2> ..."))
    try:
        user_ids = message.text.split(maxsplit=1)[1]
        c = 0
        for user_id_str in user_ids.split():
            user_id = int(user_id_str)
            c += 1
            if user_id in client.admins: continue
            if not await client.mongodb.present_user(user_id):
                await client.mongodb.add_user(user_id)
            else:
                await client.mongodb.unban_user(user_id)
        return await message.reply(ftext(f"{c} users have been unbanned!"))
    except Exception as e:
        return await message.reply(ftext(f"**Error:** {e}"))

@Client.on_callback_query(filters.regex('^close$'))
async def close(client: Client, query: CallbackQuery):
    await query.message.delete()
    try:
        if query.message.reply_to_message:
            await query.message.reply_to_message.delete()
    except Exception:
        pass

@Client.on_message(filters.command("queue") & auth_filter)
async def queue_status(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))

    total_tasks = 0
    for user_id in client.user_tasks:
        total_tasks += len(client.user_tasks[user_id])

    msg = f"<blockquote><b>📊 Queue Status</b></blockquote>\n\n"
    msg += f"<b>Total Active Tasks:</b> <code>{total_tasks}</code>\n"
    if total_tasks > 0:
        msg += f"<i>Tasks are processed one by one globally.</i>"

    await message.reply(ftext(msg))

@Client.on_message(filters.command("clear") & auth_filter)
async def clear_queue(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))

    # Clear user tasks
    client.user_tasks.clear()

    # Kill active FFmpeg processes
    from helper.anime_globals import ffpids_cache
    import os
    import signal

    killed_count = 0
    for pid in list(ffpids_cache):
        try:
            os.kill(pid, signal.SIGKILL)
            ffpids_cache.remove(pid)
            killed_count += 1
        except Exception:
            pass

    await message.reply(ftext(f"✅ <b>Queue cleared!</b>\n\n• User tasks reset.\n• <code>{killed_count}</code> active encoding processes terminated."))

@Client.on_message(filters.command("stats") & auth_filter)
async def stats_cmd(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))

    import psutil
    from helper.helper_func import get_readable_time
    import time

    # System Info
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    uptime = get_readable_time(int(time.time() - client.uptime.timestamp()))

    msg = f"""<blockquote><b>📊 System & Server Info</b></blockquote>

<b>CPU Usage:</b> <code>{cpu}%</code>
<b>RAM Usage:</b> <code>{mem}%</code>
<b>Disk Usage:</b> <code>{disk}%</code>
<b>Bot Uptime:</b> <code>{uptime}</code>

<b>Running on Version:</b> <code>v1.0.0</code>"""
    await message.reply(ftext(msg))

@Client.on_message(filters.command("restart") & auth_filter)
async def restart_cmd(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))

    from helper.helper_func import graceful_restart
    await graceful_restart(client, message)
