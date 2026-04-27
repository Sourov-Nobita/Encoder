from helper.utils import auth_filter
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.enums import ParseMode
from helper.helper_func import font_shaper, ftext, flbl, graceful_restart
from helper.custom_listen import ListenerTimeout
import os

DEFAULT_SETTINGS_PHOTO = "https://envs.sh/YsH.jpg"

async def edit_settings_reply(client, query, msg, reply_markup):
    photo = client.messages.get('SETTINGS_PHOTO', DEFAULT_SETTINGS_PHOTO)
    if query.message.photo:
        await query.message.edit_media(media=InputMediaPhoto(media=photo, caption=msg), reply_markup=reply_markup)
    else:
        try:
            await query.message.delete()
        except Exception:
            pass
        await client.send_photo(chat_id=query.message.chat.id, photo=photo, caption=msg, reply_markup=reply_markup)

@Client.on_message(filters.command("settings") & auth_filter)
async def settings_command(client, message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))

    # Mocking a query-like object to reuse settings_page_1
    class MockQuery:
        def __init__(self, message, user):
            self.message = message
            self.from_user = user
        async def answer(self, *args, **kwargs):
            pass

    await settings_page_1(client, MockQuery(message, message.from_user))

@Client.on_callback_query(filters.regex("^settings$"))
async def settings_main(client, query):
    await settings_page_1(client, query)

@Client.on_callback_query(filters.regex("^settings_pg1$"))
async def settings_page_1_cb(client, query):
    await settings_page_1(client, query)

async def settings_page_1(client, query):
    """Displays Page 1 of the settings menu."""
    await query.answer()
    msg = ftext("<blockquote><b>⚙️ Bot Settings (Page 1/3)</b></blockquote>\nUse the buttons below to manage the bot's core features.")

    buttons = [
        [InlineKeyboardButton(flbl("FSub Channels"), callback_data="fsub"), InlineKeyboardButton(flbl("Dump Channel"), callback_data="db_settings")],
        [InlineKeyboardButton(flbl("Log Channel"), callback_data="set_log_ch"), InlineKeyboardButton(flbl("Admins"), callback_data="admins")],
        [InlineKeyboardButton(flbl("Home"), callback_data="home"), InlineKeyboardButton(flbl("Next »"), callback_data="settings_pg2")]
    ]

    reply_markup = InlineKeyboardMarkup(buttons)
    await edit_settings_reply(client, query, msg, reply_markup)

@Client.on_callback_query(filters.regex("^restart_bot$"))
async def restart_bot_cb(client, query):
    if query.from_user.id not in client.admins:
        return await query.answer(ftext("Admin only!"), show_alert=True)
    await graceful_restart(client, query)

@Client.on_callback_query(filters.regex("^settings_help$"))
async def settings_help_cb(client, query):
    await query.answer()
    help_text = ftext("""<blockquote><b>❓ Settings Help</b></blockquote>

Welcome to the Settings Panel!

• <b>FSub Channels:</b> Manage Force Subscribe channels.
• <b>Dump Channel:</b> Manage Dump channel for file storage.
• <b>Admins:</b> Add or remove bot admins.
• <b>Files Settings:</b> Toggle Content Protection and Hide Caption.
• <b>Photos & Texts:</b> Customize bot media and messages.
• <b>Encode Settings:</b> Choose default quality for encoding.

Use the navigation buttons to move through pages.""")
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(flbl("« Back"), callback_data="settings_pg1")]])
    await edit_settings_reply(client, query, help_text, reply_markup)

@Client.on_callback_query(filters.regex("^settings_pg2$"))
async def settings_page_2(client, query):
    """Displays Page 2 of the settings menu."""
    await query.answer()
    msg = ftext("<blockquote><b>⚙️ Bot Settings (Page 2/3)</b></blockquote>\nUse the buttons below to manage the bot's core features.")

    buttons = [
        [InlineKeyboardButton(flbl("Mode Settings"), callback_data="mode_settings"), InlineKeyboardButton(flbl("Files Settings"), callback_data="file_settings")],
        [InlineKeyboardButton(flbl("Gofile Settings"), callback_data="gofile_settings")],
        [InlineKeyboardButton(flbl("Photos"), callback_data="photos"), InlineKeyboardButton(flbl("Texts"), callback_data="texts")],
        [InlineKeyboardButton(flbl("« Back"), callback_data="settings_pg1"), InlineKeyboardButton(flbl("Next »"), callback_data="settings_pg3")]
    ]

    reply_markup = InlineKeyboardMarkup(buttons)
    await edit_settings_reply(client, query, msg, reply_markup)

@Client.on_callback_query(filters.regex("^settings_pg3$"))
async def settings_page_3(client, query):
    """Displays Page 3 of the settings menu."""
    await query.answer()
    msg = ftext("<blockquote><b>⚙️ Bot Settings (Page 3/3)</b></blockquote>\nUse the buttons below to manage the bot's core features.")

    buttons = [
        [InlineKeyboardButton(flbl("MongoDB Settings"), callback_data="mongodb_settings")],
        [InlineKeyboardButton(flbl("Restart Bot"), callback_data="restart_bot")]
    ]

    buttons.append([InlineKeyboardButton(flbl("« Back"), callback_data="settings_pg2"), InlineKeyboardButton(flbl("Home"), callback_data="home")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await edit_settings_reply(client, query, msg, reply_markup)


@Client.on_callback_query(filters.regex("^file_settings$"))
async def file_settings_cb(client, query):
    from plugins.file_settings import file_settings_panel
    await file_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^mongodb_settings$"))
async def mongodb_settings_cb(client, query):
    from plugins.mongodb_settings import mongodb_settings_panel
    await mongodb_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^fsub$"))
async def fsub_settings_cb(client, query):
    from plugins.force_sub import fsub
    await fsub(client, query)

@Client.on_callback_query(filters.regex("^db_settings$"))
async def db_settings_cb(client, query):
    from plugins.database_settings import db_settings
    await db_settings(client, query)

@Client.on_callback_query(filters.regex("^admins$"))
async def admins_settings_cb(client, query):
    from plugins.admins import admins
    await admins(client, query)

def get_photos_status(client):
    added_text = ftext('Added')
    not_added_text = ftext('Not added')
    status = f"<b>>> Start Photo :</b> <code>{added_text if client.messages.get('START_PHOTO') else not_added_text}</code>\n"
    status += f"<b>>> FSub Photo :</b> <code>{added_text if client.messages.get('FSUB_PHOTO') else not_added_text}</code>\n"
    status += f"<b>>> Help Photo :</b> <code>{added_text if client.messages.get('HELP_PHOTO') else not_added_text}</code>\n"
    status += f"<b>>> Settings Photo :</b> <code>{added_text if client.messages.get('SETTINGS_PHOTO') else not_added_text}</code>\n"
    status += f"<b>>> About Photo :</b> <code>{added_text if client.messages.get('ABOUT_PHOTO') else not_added_text}</code>"
    return status

@Client.on_callback_query(filters.regex(r"^photos(_pg\d+)?$"))
async def photos_cb(client, query):
    page = 1
    if query.matches and query.matches[0].group(1):
        page = int(query.matches[0].group(1).replace("_pg", ""))

    if page == 1:
        await photos_page_1(client, query)
    elif page == 2:
        await photos_page_2(client, query)
    elif page == 3:
        await photos_page_3(client, query)

async def photos_page_1(client, query):
    msg = ftext("<blockquote><b>🖼️ Media & Photos (Page 1/3)</b></blockquote>\nSet or remove the images used in the bot's messages.\n\n") + get_photos_status(client)
    set_text, change_text, remove_text = 'Set', 'Change', 'Remove'

    buttons = [
        [
            InlineKeyboardButton(flbl((set_text if not client.messages.get("START_PHOTO") else change_text) + ' Start Pic'), callback_data='add_start_photo'),
            InlineKeyboardButton(flbl((set_text if not client.messages.get("FSUB_PHOTO") else change_text) + ' FSub Pic'), callback_data='add_fsub_photo')
        ],
        [
            InlineKeyboardButton(flbl(remove_text + ' Start Pic'), callback_data='rm_start_photo'),
            InlineKeyboardButton(flbl(remove_text + ' FSub Pic'), callback_data='rm_fsub_photo')
        ],
        [InlineKeyboardButton(flbl("« Back"), callback_data='settings_pg2'), InlineKeyboardButton(flbl("Next »"), callback_data='photos_pg2')]
    ]
    await edit_settings_reply(client, query, msg, InlineKeyboardMarkup(buttons))

async def photos_page_2(client, query):
    msg = ftext("<blockquote><b>🖼️ Media & Photos (Page 2/3)</b></blockquote>\nSet or remove the images used in the bot's messages.\n\n") + get_photos_status(client)
    set_text, change_text, remove_text = 'Set', 'Change', 'Remove'

    buttons = [
        [
            InlineKeyboardButton(flbl((set_text if not client.messages.get("HELP_PHOTO") else change_text) + ' Help Pic'), callback_data='add_help_photo'),
            InlineKeyboardButton(flbl((set_text if not client.messages.get("SETTINGS_PHOTO") else change_text) + ' Settings Pic'), callback_data='add_settings_photo')
        ],
        [
            InlineKeyboardButton(flbl(remove_text + ' Help Pic'), callback_data='rm_help_photo'),
            InlineKeyboardButton(flbl(remove_text + ' Settings Pic'), callback_data='rm_settings_photo')
        ],
        [InlineKeyboardButton(flbl("« Back"), callback_data='photos_pg1'), InlineKeyboardButton(flbl("Next »"), callback_data='photos_pg3')]
    ]
    await edit_settings_reply(client, query, msg, InlineKeyboardMarkup(buttons))

async def photos_page_3(client, query):
    msg = ftext("<blockquote><b>🖼️ Media & Photos (Page 3/3)</b></blockquote>\nSet or remove the images used in the bot's messages.\n\n") + get_photos_status(client)
    set_text, change_text, remove_text = 'Set', 'Change', 'Remove'

    buttons = [
        [
            InlineKeyboardButton(flbl((set_text if not client.messages.get("ABOUT_PHOTO") else change_text) + ' About Pic'), callback_data='add_about_photo'),
            InlineKeyboardButton(flbl(remove_text + ' About Pic'), callback_data='rm_about_photo')
        ],
        [InlineKeyboardButton(flbl("« Back"), callback_data='photos_pg2'), InlineKeyboardButton(flbl("Home"), callback_data='home')]
    ]
    await edit_settings_reply(client, query, msg, InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^texts$"))
async def texts_settings_cb(client, query):
    from plugins.texts import texts
    await texts(client, query)

@Client.on_callback_query(filters.regex('^rm_start_photo$'))
async def rm_start_photo(client, query):
    client.messages['START_PHOTO'] = ''
    await client.mongodb.save_settings(client.name, client.get_current_settings())
    await query.answer(ftext("Start Photo Removed!"), show_alert=True)
    await photos_page_1(client, query)

@Client.on_callback_query(filters.regex('^rm_fsub_photo$'))
async def rm_fsub_photo(client, query):
    client.messages['FSUB_PHOTO'] = ''
    await client.mongodb.save_settings(client.name, client.get_current_settings())
    await query.answer(ftext("FSub Photo Removed!"), show_alert=True)
    await photos_page_1(client, query)

async def handle_photo_update(client, query, photo_key, prompt_text, page=1):
    await query.answer()
    prompt_message = await query.message.edit_text(ftext(prompt_text), parse_mode=ParseMode.HTML)
    back_cb = f"photos_pg{page}"
    try:
        res = await client.listen(chat_id=query.from_user.id, filters=filters.text, timeout=60)
        
        photo_val = ""
        if res.text and (res.text.startswith('https://') or res.text.startswith('http://')):
            photo_val = res.text
        
        if photo_val:
            client.messages[photo_key] = photo_val
            await client.mongodb.save_settings(client.name, client.get_current_settings())
            title = ftext(photo_key.replace('_', ' ').title())
            await query.message.edit_text(ftext(f"✅ ") + title + ftext(f" has been updated!"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(flbl('« Back'), back_cb)]]), parse_mode=ParseMode.HTML)
        else:
            await query.message.edit_text(ftext("❌ Invalid input. Please send a photo or a valid URL."), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(flbl('« Back'), back_cb)]]), parse_mode=ParseMode.HTML)
    except ListenerTimeout:
        await prompt_message.edit_text(ftext("<b>Timeout! No changes were made.</b>"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(flbl('« Back'), back_cb)]]), parse_mode=ParseMode.HTML)

@Client.on_callback_query(filters.regex("^add_start_photo$"))
async def add_start_photo(client, query):
    await handle_photo_update(client, query, 'START_PHOTO', "<blockquote>Please send the <b>Photo URL</b> for the <b>Start Message</b>. (Direct pictures are not allowed)</blockquote>", page=1)

@Client.on_callback_query(filters.regex("^add_fsub_photo$"))
async def add_fsub_photo(client, query):
    await handle_photo_update(client, query, 'FSUB_PHOTO', "<blockquote>Please send the <b>Photo URL</b> for the <b>Force Subscribe Message</b>. (Direct pictures are not allowed)</blockquote>", page=1)

@Client.on_callback_query(filters.regex('^rm_help_photo$'))
async def rm_help_photo(client, query):
    client.messages['HELP_PHOTO'] = ''
    await client.mongodb.save_settings(client.name, client.get_current_settings())
    await query.answer(ftext("Help Photo Removed!"), show_alert=True)
    await photos_page_2(client, query)

@Client.on_callback_query(filters.regex("^add_help_photo$"))
async def add_help_photo(client, query):
    await handle_photo_update(client, query, 'HELP_PHOTO', "<blockquote>Please send the <b>Photo URL</b> for the <b>Help Message</b>. (Direct pictures are not allowed)</blockquote>", page=2)

@Client.on_callback_query(filters.regex('^rm_settings_photo$'))
async def rm_settings_photo(client, query):
    client.messages['SETTINGS_PHOTO'] = ''
    await client.mongodb.save_settings(client.name, client.get_current_settings())
    await query.answer(ftext("Settings Photo Removed!"), show_alert=True)
    await photos_page_2(client, query)

@Client.on_callback_query(filters.regex("^add_settings_photo$"))
async def add_settings_photo(client, query):
    await handle_photo_update(client, query, 'SETTINGS_PHOTO', "<blockquote>Please send the <b>Photo URL</b> for the <b>Settings Panel</b>. (Direct pictures are not allowed)</blockquote>", page=2)

@Client.on_callback_query(filters.regex('^rm_about_photo$'))
async def rm_about_photo(client, query):
    client.messages['ABOUT_PHOTO'] = ''
    await client.mongodb.save_settings(client.name, client.get_current_settings())
    await query.answer(ftext("About Photo Removed!"), show_alert=True)
    await photos_page_3(client, query)

@Client.on_callback_query(filters.regex("^add_about_photo$"))
async def add_about_photo(client, query):
    await handle_photo_update(client, query, 'ABOUT_PHOTO', "<blockquote>Please send the <b>Photo URL</b> for the <b>About Message</b>. (Direct pictures are not allowed)</blockquote>", page=3)

@Client.on_callback_query(filters.regex("^set_log_ch$"))
async def set_log_ch_cb(client, query):
    if query.from_user.id not in client.admins:
        return await query.answer(ftext("Admin only!"), show_alert=True)

    await query.message.delete()
    prompt = await client.send_message(query.from_user.id, ftext("<blockquote><b>Send Log Channel ID (e.g. -100xxx):</b></blockquote>"))
    try:
        res = await client.listen(chat_id=query.from_user.id, filters=filters.text, timeout=60)
        ch_id = int(res.text.strip())
        await client.mongodb.save_bot_setting('log_channel', ch_id)
        client.log_channel = ch_id
        await res.reply(ftext(f"✅ <b>Log Channel ID updated to:</b> <code>{ch_id}</code>"))
    except ListenerTimeout:
        await client.send_message(query.from_user.id, ftext("❌ <b>Timeout!</b> No changes made."))
    except ValueError:
        await client.send_message(query.from_user.id, ftext("❌ <b>Invalid ID!</b> Please send a numeric ID."))
    except Exception as e:
        await client.send_message(query.from_user.id, ftext(f"❌ <b>Error:</b> {e}"))

    await settings_page_1(client, query)


@Client.on_callback_query(filters.regex("^mode_settings$"))
async def mode_settings_cb(client, query):
    await query.answer()
    current_mode = getattr(client, "bot_mode", "auto_encode")

    is_auto_enc = current_mode in ["auto_encode", "encode"]
    display_mode = "Auto Encode" if is_auto_enc else current_mode.replace('_', ' ').capitalize()

    msg = ftext(f"<blockquote><b>⚙️ Mode Settings</b></blockquote>\n\n<b>Current Mode:</b> <code>{display_mode}</code>\n\nChoose the bot's operation mode:")

    buttons = [
        [InlineKeyboardButton(flbl("Auto Encode" + (" ✅" if is_auto_enc else "")), callback_data="set_mode_auto_encode")],
        [InlineKeyboardButton(flbl("Auto Rename" + (" ✅" if current_mode == "auto_rename" else "")), callback_data="set_mode_auto_rename"),
         InlineKeyboardButton(flbl("Manual Rename" + (" ✅" if current_mode == "manual_rename" else "")), callback_data="set_mode_manual_rename")],
        [InlineKeyboardButton(flbl("« Back"), callback_data="settings_pg2")]
    ]

    await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^set_mode_(auto_encode|auto_rename|manual_rename)$"))
async def set_bot_mode_cb(client, query):
    mode = query.data.split("_", 2)[2]
    client.bot_mode = mode
    await client.mongodb.save_bot_setting("bot_mode", mode)
    await query.answer(ftext(f"Bot mode set to {mode.replace('_', ' ').capitalize()}!"))
    await mode_settings_cb(client, query)

@Client.on_callback_query(filters.regex("^gofile_settings$"))
async def gofile_settings_cb(client, query):
    await query.answer()
    user_id = query.from_user.id
    token = await client.mongodb.get_gofile_token(user_id)

    msg = ftext(f"<blockquote><b>⚙️ GoFile Settings</b></blockquote>\n\n"
                f"<b>Current Token:</b> <code>{token if token else 'Not Set'}</code>\n\n"
                f"GoFile token is used for uploading files to your GoFile account.")

    buttons = [
        [InlineKeyboardButton(flbl("Set Token"), callback_data="set_gofile_token")],
        [InlineKeyboardButton(flbl("Remove Token"), callback_data="rm_gofile_token")],
        [InlineKeyboardButton(flbl("« Back"), callback_data="settings_pg2")]
    ]

    await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

@Client.on_callback_query(filters.regex("^set_gofile_token$"))
async def set_gofile_token_cb(client, query):
    await query.answer()
    user_id = query.from_user.id

    prompt = await query.message.edit_text(ftext("<blockquote>Please send your <b>GoFile Token</b>.</blockquote>"), parse_mode=ParseMode.HTML)

    try:
        res = await client.listen(chat_id=user_id, filters=filters.text, timeout=60)
        token = res.text.strip()
        await client.mongodb.set_gofile_token(user_id, token)
        await res.reply(ftext(f"✅ **GoFile Token updated successfully!**"))
    except ListenerTimeout:
        await query.message.reply(ftext("❌ **Timeout!** No changes made."))
    except Exception as e:
        await query.message.reply(ftext(f"❌ **Error:** {e}"))

    await gofile_settings_cb(client, query)

@Client.on_callback_query(filters.regex("^rm_gofile_token$"))
async def rm_gofile_token_cb(client, query):
    user_id = query.from_user.id
    await client.mongodb.set_gofile_token(user_id, None)
    await query.answer("GoFile Token Removed!", show_alert=True)
    await gofile_settings_cb(client, query)
