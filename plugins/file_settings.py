from helper.utils import auth_filter
from helper.helper_func import font_shaper, ftext, flbl
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.enums import ParseMode
from helper.custom_listen import ListenerTimeout
from plugins.settings import DEFAULT_SETTINGS_PHOTO

@Client.on_callback_query(filters.regex("^file_settings$"))
async def file_settings_entry(client: Client, query: CallbackQuery):
    await query.answer()
    await file_settings_panel(client, query)

async def file_settings_panel(client: Client, query: CallbackQuery):
    """Generates and displays the Files Related Settings panel."""
    
    upload_as_doc = getattr(client, 'upload_as_doc', False)
    thumbnail = getattr(client, 'thumbnail', None)
    metadata_enabled = getattr(client, 'metadata_status', False)

    total_files = await client.mongodb.get_total_files_count()

    metadata_status_text = ftext("Enabled ✔" if metadata_enabled else "Disabled ✘")
    file_mode = ftext("Document 📄" if upload_as_doc else "Video 🎬")
    thumb_status = ftext("Added ✔" if thumbnail else "Not Added ✘")
    
    caption = ftext(f"""<blockquote><b>✧ Files Related Settings</b></blockquote>
<pre><b>🏷️ Metadata: {metadata_status_text}</b></pre>
<pre><b>📁 File Mode: {file_mode}</b></pre>
<pre><b>🖼️ Thumbnail: {thumb_status}</b></pre>
<blockquote><b>📊 Bot Analytics</b>
<b>>> Total Files:</b> <code>{total_files}</code></blockquote>\n
<b>Click below buttons to change settings</b>""")

    file_mode_btn_text = f"Mode: {'Video' if upload_as_doc else 'Document'}"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(flbl(f"Metadata: {'✔' if not metadata_enabled else '✘'}"), callback_data="toggle_metadata"), InlineKeyboardButton(flbl(file_mode_btn_text), callback_data="toggle_file_mode")],
        [InlineKeyboardButton(flbl("Set Thumb"), callback_data="set_thumb"), InlineKeyboardButton(flbl("Del Thumb"), callback_data="del_thumb")],
        [InlineKeyboardButton(flbl("« Back"), callback_data="settings_pg3"), InlineKeyboardButton(flbl("Close"), callback_data="close")]
    ])
    
    photo = client.messages.get('SETTINGS_PHOTO', DEFAULT_SETTINGS_PHOTO)
    try:
        if query.message.photo:
            await query.message.edit_media(media=InputMediaPhoto(media=photo, caption=caption), reply_markup=reply_markup)
        else:
            await query.message.delete()
            await client.send_photo(chat_id=query.message.chat.id, photo=photo, caption=caption, reply_markup=reply_markup)
    except Exception as e:
        client.LOGGER(__name__, client.name).error(f"Error in file_settings_panel: {e}")


@Client.on_callback_query(filters.regex("^toggle_metadata$"))
async def toggle_metadata(client: Client, query: CallbackQuery):
    client.metadata_status = not getattr(client, 'metadata_status', False)
    await client.mongodb.save_bot_setting('metadata_status', client.metadata_status)
    # Also update for individual user to maintain consistency if they use it
    await client.mongodb.set_user_setting(query.from_user.id, "metadata_status", client.metadata_status)
    await query.answer(ftext(f"Metadata is now {'ENABLED' if client.metadata_status else 'DISABLED'}"))
    await file_settings_panel(client, query)



@Client.on_callback_query(filters.regex("^toggle_file_mode$"))
async def toggle_file_mode(client: Client, query: CallbackQuery):
    client.upload_as_doc = not getattr(client, 'upload_as_doc', False)
    await client.mongodb.save_bot_setting('upload_as_doc', client.upload_as_doc)
    await query.answer(ftext(f"File Mode is now {'DOCUMENT' if client.upload_as_doc else 'VIDEO'}"))
    await file_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^set_thumb$"))
async def set_thumb(client: Client, query: CallbackQuery):
    await query.answer()
    await query.message.delete()

    prompt = await client.send_message(
        query.from_user.id,
        ftext("<blockquote>Please send the <b>Photo URL</b> (starting with http/https) to set as the custom thumbnail.</blockquote>\n\nType /cancel to abort."),
        parse_mode=ParseMode.HTML
    )
    try:
        res = await client.listen(chat_id=query.from_user.id, filters=filters.text, timeout=120)
        if res.text and (res.text or "").lower() == "/cancel":
            await res.reply(ftext("🚫 Action cancelled."))
        elif res.text and res.text.startswith(("http://", "https://")):
            file_url = res.text.strip()

            # Download and save as bot-specific thumb path for helper modules
            import os
            from helper.anime_utils import get_session
            session = await get_session()
            temp_path = f"temp_{client.username}_thumb.jpg"
            try:
                async with session.get(file_url) as resp:
                    if resp.status == 200:
                        with open(temp_path, 'wb') as f:
                            f.write(await resp.read())
                        if os.path.exists(client.thumb_path): os.remove(client.thumb_path)
                        os.rename(temp_path, client.thumb_path)

                        client.thumbnail = file_url
                        await client.mongodb.save_bot_setting('thumbnail', file_url)
                        await res.reply(ftext("✔ Custom thumbnail has been updated successfully!"))
                    else:
                        await res.reply(ftext(f"❌ Failed to download image. Status: {resp.status}"))
            except Exception as e:
                await res.reply(ftext(f"❌ Error downloading image: {e}"))
                if os.path.exists(temp_path): os.remove(temp_path)
        else:
            await res.reply(ftext("❌ Invalid input. Please send a valid image URL starting with http/https."))
    except ListenerTimeout:
        await prompt.edit(ftext("<b>Timeout! No changes were made.</b>"))

    dummy_msg = await client.send_message(query.from_user.id, "Loading...")
    query.message = dummy_msg
    await file_settings_panel(client, query)
    await dummy_msg.delete()

@Client.on_callback_query(filters.regex("^del_thumb$"))
async def del_thumb(client: Client, query: CallbackQuery):
    client.thumbnail = None
    await client.mongodb.save_bot_setting('thumbnail', None)

    import os
    if os.path.exists(client.thumb_path):
        os.remove(client.thumb_path)

    await query.answer("✔ Custom thumbnail has been removed.", show_alert=True)
    await file_settings_panel(client, query)
