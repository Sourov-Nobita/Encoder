from helper.utils import auth_filter
from helper.helper_func import font_shaper, ftext, flbl
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.enums import ParseMode
from helper.custom_listen import ListenerTimeout

@Client.on_callback_query(filters.regex("^mongodb_settings$"))
async def mongodb_settings_panel(client: Client, query: CallbackQuery | Message):
    user_id = query.from_user.id
    if user_id not in client.admins:
        if isinstance(query, CallbackQuery): await query.answer(ftext("Admin only!"), show_alert=True)
        return

    if isinstance(query, CallbackQuery): await query.answer()

    bot_config = await client.mongodb.get_bot_config(client.username)
    uris = bot_config.get("db_uris", [])

    caption = ftext("<blockquote><b>🍃 MongoDB Settings</b></blockquote>\n\n")
    buttons = []

    current_count = len(uris)

    # Bot case: 1 default + up to 2 extra
    default_stats = await client.mongodb.get_mongodb_stats(client.initial_db_uri)
    caption += ftext("<b>✨ Default MongoDB:</b>\n") + f"<code>{client.initial_db_uri[:30]}...</code>\n"
    caption += ftext("<b>Status:</b> ") + f"<code>{default_stats['status']}</code>\n"
    caption += ftext("<b>Size:</b> ") + f"<code>{default_stats['size']}</code> | " + ftext("<b>DBs:</b> ") + f"<code>{default_stats['databases']}</code>\n\n"

    for i, uri in enumerate(uris, 1):
        stats = await client.mongodb.get_mongodb_stats(uri)
        caption += ftext(f"<b>{i}. Extra MongoDB:</b>\n") + f"<code>{uri[:30]}...</code>\n"
        caption += ftext("<b>Status:</b> ") + f"<code>{stats['status']}</code>\n"
        caption += ftext("<b>Size:</b> ") + f"<code>{stats['size']}</code> | " + ftext("<b>DBs:</b> ") + f"<code>{stats['databases']}</code>\n\n"
        buttons.append([InlineKeyboardButton(flbl(f"Remove Extra {i}"), callback_data=f"remove_mongodb_{i-1}")])

    if current_count < 2:
        buttons.append([InlineKeyboardButton(flbl("Add Extra MongoDB"), callback_data="add_mongodb_uri")])

    buttons.append([InlineKeyboardButton(flbl("« Back"), callback_data="settings_pg5")])

    reply_markup = InlineKeyboardMarkup(buttons)

    message = query.message if isinstance(query, CallbackQuery) else query
    if message.photo:
        await message.edit_caption(caption=caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await message.edit_text(text=caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

@Client.on_callback_query(filters.regex("^add_mongodb_uri$"))
async def add_mongodb_uri(client: Client, query: CallbackQuery):
    await query.message.delete()
    prompt = await client.send_message(query.from_user.id, ftext("<blockquote><b>Send your custom MongoDB URI:</b>\n\nExample: <code>mongodb+srv://user:pass@cluster.mongodb.net/dbname?retryWrites=true&w=majority</code></blockquote>"))

    try:
        res = await client.listen(chat_id=query.from_user.id, filters=filters.text, timeout=120)
        uri = res.text.strip()

        if not uri.startswith("mongodb"):
             return await res.reply(ftext("❌ Invalid MongoDB URI format."))

        # Limit is 2 for bot extra URIs
        bot_config = await client.mongodb.get_bot_config(client.username)
        uris = bot_config.get("db_uris", [])
        limit = 2

        if len(uris) >= limit:
            return await res.reply(ftext(f"❌ <b>Limit reached!</b> You can only set up to {limit} extra URIs."))

        success = await client.mongodb.add_bot_uri(client.username, uri)
        await client.mongodb.add_bot_uri(client.name, uri)

        if success:
            await res.reply(ftext("✅ <b>MongoDB URI added!</b>\n\n<i>Note: Restart the bot for changes to take effect.</i>"))
        else:
            await res.reply(ftext("❌ <b>Failed to add URI.</b>"))
    except ListenerTimeout:
        await client.send_message(query.from_user.id, ftext("<b>Timeout! No changes were made.</b>"))
    except Exception as e:
        await client.send_message(query.from_user.id, ftext(f"❌ Error: {e}"))

    await mongodb_settings_panel(client, await client.send_message(query.from_user.id, ftext("Loading...")))

@Client.on_callback_query(filters.regex(r"^remove_mongodb_(\d+)$"))
async def remove_mongodb_uri(client: Client, query: CallbackQuery):
    index = int(query.matches[0].group(1))
    await client.mongodb.remove_bot_uri(client.username, index)
    await client.mongodb.remove_bot_uri(client.name, index)
    await query.answer(ftext("✅ Removed MongoDB URI."), show_alert=True)
    await mongodb_settings_panel(client, query)
