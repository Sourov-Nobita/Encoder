from helper.utils import auth_filter
from helper.helper_func import ftext, flbl
import asyncio
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from helper.custom_listen import ListenerTimeout
from plugins.settings import DEFAULT_SETTINGS_PHOTO

async def get_db_settings_panel(client: Client):
    """Generates the photo, text, and markup for the Dump Channel settings panel."""
    photo_url = client.messages.get('SETTINGS_PHOTO', DEFAULT_SETTINGS_PHOTO)
    
    dump_channel = getattr(client, 'dump_channel', None)

    async def get_chat_title(chat_id):
        if not chat_id: return "Not Set"
        try:
            chat = await client.get_chat(chat_id)
            return f"{chat.title} (<code>{chat_id}</code>)"
        except Exception:
            return f"Invalid Channel (<code>{chat_id}</code>)"

    dump_text = await get_chat_title(dump_channel)

    caption_text = ftext(f"""<blockquote><b>✧ Dump Channel Settings</b></blockquote>
<b>>> Current Dump Channel:</b>
>> {dump_text}

Every encoded or output file will be stored in this channel.""")

    buttons = [
        [InlineKeyboardButton(flbl('Set Dump Channel'), 'set_dump_ch'), InlineKeyboardButton(flbl('Remove Dump Channel'), 'rm_dump_ch')]
    ]

    buttons.append([InlineKeyboardButton(flbl('« Back'), 'settings_pg1')])
    reply_markup = InlineKeyboardMarkup(buttons)
    
    return photo_url, caption_text, reply_markup

@Client.on_message(filters.command('database') & auth_filter)
async def db_settings_command(client: Client, message: Message):
    """Handles the /database command."""
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))
    
    photo, caption, reply_markup = await get_db_settings_panel(client)
    
    if photo:
        await message.reply_photo(photo=photo, caption=caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def db_settings(client: Client, query: CallbackQuery):
    """
    Displays the Dump Channel settings menu from a callback.
    """
    await query.answer()
    photo, caption, reply_markup = await get_db_settings_panel(client)
    
    if photo and not query.message.photo:
        await query.message.delete()
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=photo,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    elif photo and query.message.photo:
         await query.message.edit_caption(caption=caption, reply_markup=reply_markup)
    else:
        await query.message.edit_text(caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

@Client.on_callback_query(filters.regex("^set_dump_ch$"))
async def set_dump_ch_cb(client: Client, query: CallbackQuery):
    await query.answer()
    
    prompt_msg_text = ftext("<blockquote>Send the <b>Channel ID</b> for the Dump channel (e.g. -100xxx):</blockquote>")

    if query.message.photo:
        await query.message.edit_caption(caption=prompt_msg_text)
    else:
        await query.message.edit_text(prompt_msg_text, reply_markup=None, parse_mode=ParseMode.HTML)

    try:
        response = await client.listen(chat_id=query.from_user.id, filters=filters.text, timeout=90)
        channel_id = int(response.text.strip())

        # Basic verification - check if bot is admin
        from helper.helper_func import is_bot_admin
        is_admin, reason = await is_bot_admin(client, channel_id)
        if not is_admin:
            await response.reply(ftext(f"❌ <b>Error:</b> {reason}"), parse_mode=ParseMode.HTML)
        else:
            client.dump_channel = channel_id
            await client.mongodb.save_bot_setting('dump_channel', channel_id)
            await response.reply(ftext(f"✅ <b>Dump Channel updated to:</b> <code>{channel_id}</code>"), parse_mode=ParseMode.HTML)
        
    except ListenerTimeout:
         pass
    except (ValueError, TypeError):
        await client.send_message(query.from_user.id, ftext("❌ <b>Invalid ID format.</b> Please send a correct Channel ID."), parse_mode=ParseMode.HTML)
    except Exception as e:
        await client.send_message(query.from_user.id, ftext(f"❌ An error occurred: <code>{e}</code>"), parse_mode=ParseMode.HTML)
    
    await db_settings(client, query)

@Client.on_callback_query(filters.regex("^rm_dump_ch$"))
async def rm_dump_ch_cb(client: Client, query: CallbackQuery):
    client.dump_channel = None
    await client.mongodb.save_bot_setting('dump_channel', None)
    await query.answer("✅ Dump Channel removed.", show_alert=True)
    await db_settings(client, query)

@Client.on_callback_query(filters.regex("^db_settings$"))
async def db_settings_cb(client: Client, query: CallbackQuery):
    await db_settings(client, query)
