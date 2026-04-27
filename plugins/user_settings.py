from helper.utils import auth_filter
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.enums import ParseMode
from helper.helper_func import ftext, flbl
from helper.custom_listen import ListenerTimeout

DEFAULT_SETTINGS_PHOTO = "https://envs.sh/YsH.jpg"

async def edit_user_settings_reply(client, query, msg, reply_markup):
    photo = client.messages.get('SETTINGS_PHOTO', DEFAULT_SETTINGS_PHOTO)
    if query.message.photo:
        try:
            await query.message.edit_media(media=InputMediaPhoto(media=photo, caption=msg), reply_markup=reply_markup)
        except Exception:
            await query.message.edit_caption(caption=msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await query.message.edit_text(text=msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def show_user_setting_prompt(client, query, text):
    if query.message.photo:
        return await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML)
    return await query.message.edit_text(text=text, parse_mode=ParseMode.HTML)

@Client.on_message(filters.command("usersettings") & auth_filter)
async def user_settings_command(client, message):
    await user_settings_panel(client, message)

async def user_settings_panel(client, message_or_query):
    user_id = message_or_query.from_user.id

    # Load user settings
    format_template = await client.mongodb.get_format_template(user_id) or "Not Set"
    media_pref = await client.mongodb.get_media_preference(user_id) or "document"
    metadata_status = await client.mongodb.get_metadata_status(user_id)
    caption = await client.mongodb.get_caption(user_id)
    thumbnail = await client.mongodb.get_thumbnail(user_id)
    upload_mode = await client.mongodb.get_upload_mode(user_id) or "pm"
    upload_channel = await client.mongodb.get_upload_channel(user_id)
    encode_quality = await client.mongodb.get_user_setting(user_id, "encode_quality", "all")
    auto_encode = await client.mongodb.get_user_setting(user_id, "auto_encode", False)

    status_text = ftext(f"""<blockquote><b>⚙️ User Settings</b></blockquote>
<b>🏷️ Rename Format:</b> <code>{format_template}</code>
<b>📁 Media Type:</b> <code>{media_pref.capitalize()}</code>
<b>🏷️ Metadata:</b> <code>{'Enabled ✅' if metadata_status else 'Disabled ❌'}</code>
<b>📝 Custom Caption:</b> <code>{'Set ✅' if caption else 'Not Set ❌'}</code>
<b>🖼️ Custom Thumbnail:</b> <code>{'Set ✅' if thumbnail else 'Not Set ❌'}</code>
<b>📤 Upload Mode:</b> <code>{upload_mode.upper()}</code>
<b>⚙️ Encode Quality:</b> <code>{encode_quality.upper() if encode_quality != 'all' else 'All'}</code>
<b>⚙️ Auto Encode:</b> <code>{'Enabled ✅' if auto_encode else 'Disabled ❌'}</code>
{'<b>📡 Channel ID:</b> <code>' + str(upload_channel) + '</code>' if upload_mode == "channel" else ""}""")

    buttons = [
        [InlineKeyboardButton(flbl("Rename Format"), callback_data="user_set_format"),
         InlineKeyboardButton(flbl("Custom Caption"), callback_data="user_set_caption")],
        [InlineKeyboardButton(flbl(f"Media: {media_pref.capitalize()}"), callback_data="user_toggle_media"),
         InlineKeyboardButton(flbl(f"Metadata: {'ON' if metadata_status else 'OFF'}"), callback_data="user_toggle_metadata")],
        [InlineKeyboardButton(flbl("Set Thumbnail"), callback_data="user_set_thumb"),
         InlineKeyboardButton(flbl("Del Thumbnail"), callback_data="user_del_thumb")],
        [InlineKeyboardButton(flbl(f"Upload: {upload_mode.upper()}"), callback_data="user_toggle_upload"),
         InlineKeyboardButton(flbl(f"Quality: {encode_quality.upper() if encode_quality != 'all' else 'All'}"), callback_data="user_set_quality")],
        [InlineKeyboardButton(flbl(f"Auto Encode: {'ON' if auto_encode else 'OFF'}"), callback_data="user_toggle_autoencode")],
        [InlineKeyboardButton(flbl("Close"), callback_data="close")]
    ]

    if upload_mode == "channel":
        buttons.insert(4, [InlineKeyboardButton(flbl("Set Channel ID"), callback_data="user_set_channel")])

    buttons.insert(-1, [InlineKeyboardButton(flbl("Encoding Settings"), callback_data="user_enc_settings")])

    reply_markup = InlineKeyboardMarkup(buttons)
    photo = client.messages.get('SETTINGS_PHOTO', DEFAULT_SETTINGS_PHOTO)

    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.answer()
        await edit_user_settings_reply(client, message_or_query, status_text, reply_markup)
    else:
        photo = client.messages.get('SETTINGS_PHOTO', DEFAULT_SETTINGS_PHOTO)
        await client.send_photo(chat_id=message_or_query.chat.id, photo=photo, caption=status_text, reply_markup=reply_markup)

@Client.on_callback_query(filters.regex("^user_toggle_media$"))
async def user_toggle_media_cb(client, query):
    user_id = query.from_user.id
    current = await client.mongodb.get_media_preference(user_id) or "document"
    new_pref = "video" if current == "document" else "document"
    await client.mongodb.set_media_preference(user_id, new_pref)
    await user_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^user_toggle_metadata$"))
async def user_toggle_metadata_cb(client, query):
    user_id = query.from_user.id
    current = await client.mongodb.get_metadata_status(user_id)
    await client.mongodb.set_user_setting(user_id, "metadata_status", not current)
    await user_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^user_toggle_upload$"))
async def user_toggle_upload_cb(client, query):
    user_id = query.from_user.id
    current = await client.mongodb.get_upload_mode(user_id) or "pm"
    new_mode = "channel" if current == "pm" else "pm"
    await client.mongodb.set_user_setting(user_id, "upload_mode", new_mode)
    await user_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^user_toggle_autoencode$"))
async def user_toggle_autoencode_cb(client, query):
    user_id = query.from_user.id
    current = await client.mongodb.get_user_setting(user_id, "auto_encode", False)
    await client.mongodb.set_user_setting(user_id, "auto_encode", not current)
    await user_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^user_set_format$"))
async def user_set_format_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    text = ftext("<blockquote><b>Send your new Auto Rename Format.</b>\n\nExample: <code>{filename} {quality} {episode}</code>\n\nType /cancel to abort.</blockquote>")
    msg = await show_user_setting_prompt(client, query, text)

    try:
        res = await client.listen(chat_id=query.message.chat.id, user_id=user_id, filters=filters.text, timeout=60)
        if res.text == "/cancel":
            await res.reply(ftext("🚫 Action cancelled."))
        else:
            await client.mongodb.set_format_template(user_id, res.text)
            await res.reply(ftext(f"✅ **Format updated to:** `{res.text}`"))
    except ListenerTimeout:
        await msg.edit_text(ftext("❌ **Timeout!** No changes made."))

    await user_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^user_set_caption$"))
async def user_set_caption_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    text = ftext("<blockquote><b>Send your custom caption.</b>\n\nYou can use: <code>{filename}</code>, <code>{filesize}</code>, <code>{duration}</code>\n\nType /cancel to abort or /clear to remove.</blockquote>")
    msg = await show_user_setting_prompt(client, query, text)

    try:
        res = await client.listen(chat_id=query.message.chat.id, user_id=user_id, filters=filters.text, timeout=60)
        if res.text == "/cancel":
            await res.reply(ftext("🚫 Action cancelled."))
        elif res.text == "/clear":
            await client.mongodb.set_user_setting(user_id, "caption", None)
            await res.reply(ftext("✅ **Caption removed!**"))
        else:
            await client.mongodb.set_user_setting(user_id, "caption", res.text)
            await res.reply(ftext(f"✅ **Caption updated!**"))
    except ListenerTimeout:
        await msg.edit_text(ftext("❌ **Timeout!** No changes made."))

    await user_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^user_set_channel$"))
async def user_set_channel_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    text = ftext("<blockquote><b>Send the Channel ID where you want to upload files.</b>\n\nExample: <code>-100123456789</code>\n\nType /cancel to abort.</blockquote>")
    msg = await show_user_setting_prompt(client, query, text)

    try:
        res = await client.listen(chat_id=query.message.chat.id, user_id=user_id, filters=filters.text, timeout=60)
        if res.text == "/cancel":
            await res.reply(ftext("🚫 Action cancelled."))
        else:
            try:
                ch_id = int(res.text.strip())
                await client.mongodb.set_user_setting(user_id, "upload_channel", ch_id)
                await res.reply(ftext(f"✅ **Upload Channel ID set to:** <code>{ch_id}</code>"))
            except ValueError:
                await res.reply(ftext("❌ **Invalid ID!** Please send a numeric ID."))
    except ListenerTimeout:
        await msg.edit_text(ftext("❌ **Timeout!** No changes made."))

    await user_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^user_set_thumb$"))
async def user_set_thumb_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    text = ftext("<blockquote><b>Send a Photo or a Photo URL to set as custom thumbnail.</b>\n\nType /cancel to abort.</blockquote>")
    msg = await show_user_setting_prompt(client, query, text)

    try:
        res = await client.listen(chat_id=query.message.chat.id, user_id=user_id, timeout=60)
        if res.text == "/cancel":
            await res.reply(ftext("🚫 Action cancelled."))
        elif res.photo:
            await client.mongodb.set_user_setting(user_id, "thumbnail", res.photo.file_id)
            await res.reply(ftext("✅ **Thumbnail updated via Photo!**"))
        elif res.text and res.text.startswith(("http://", "https://")):
            await client.mongodb.set_user_setting(user_id, "thumbnail", res.text.strip())
            await res.reply(ftext("✅ **Thumbnail updated via URL!**"))
        else:
            await res.reply(ftext("❌ **Invalid input!** Please send a photo or a valid URL."))
    except ListenerTimeout:
        await msg.edit_text(ftext("❌ **Timeout!** No changes made."))

    await user_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^user_del_thumb$"))
async def user_del_thumb_cb(client, query):
    user_id = query.from_user.id
    await client.mongodb.set_user_setting(user_id, "thumbnail", None)
    await query.answer("✅ Thumbnail Removed!", show_alert=True)
    await user_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^user_set_quality$"))
async def user_set_quality_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    current_quality = await client.mongodb.get_user_setting(user_id, "encode_quality", "all")

    msg = ftext(f"<blockquote><b>⚙️ Select Encode Quality</b></blockquote>\n\n"
                f"<b>Current:</b> <code>{current_quality.upper() if current_quality != 'all' else 'All'}</code>\n\n"
                f"Choose your preferred quality for encoding:")

    buttons = [
        [InlineKeyboardButton(flbl("480p" + (" ✅" if current_quality == "480" else "")), callback_data="set_user_q_480"),
         InlineKeyboardButton(flbl("720p" + (" ✅" if current_quality == "720" else "")), callback_data="set_user_q_720")],
        [InlineKeyboardButton(flbl("1080p" + (" ✅" if current_quality == "1080" else "")), callback_data="set_user_q_1080"),
         InlineKeyboardButton(flbl("All" + (" ✅" if current_quality == "all" else "")), callback_data="set_user_q_all")],
        [InlineKeyboardButton(flbl("« Back"), callback_data="user_settings_back")]
    ]

    await edit_user_settings_reply(client, query, msg, InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^set_user_q_(480|720|1080|all)$"))
async def set_user_quality_cb(client, query):
    quality = query.data.split("_")[3]
    user_id = query.from_user.id
    await client.mongodb.set_user_setting(user_id, "encode_quality", quality)
    await query.answer(f"Quality set to {quality.upper() if quality != 'all' else 'All'}!")
    await user_set_quality_cb(client, query)

@Client.on_callback_query(filters.regex("^user_settings_back$"))
async def user_settings_back_cb(client, query):
    await user_settings_panel(client, query)

@Client.on_callback_query(filters.regex("^user_enc_settings$"))
async def user_enc_settings_cb(client, query):
    user_id = query.from_user.id
    s = await client.mongodb.get_user_encode_settings(user_id)

    msg = ftext(f"<blockquote><b>⚙️ User Encoding Settings</b></blockquote>\n\n"
                f"<b>Codec:</b> <code>{s.get('codec')}</code>\n"
                f"<b>CRF:</b> <code>{s.get('crf')}</code>\n"
                f"<b>Preset:</b> <code>{s.get('preset')}</code>\n"
                f"<b>Audio Codec:</b> <code>{s.get('audio_codec')}</code>\n"
                f"<b>Audio Bitrate:</b> <code>{s.get('audio_bitrate')}</code>\n"
                f"<b>Bit Depth:</b> <code>{s.get('bit_depth')}</code>\n"
                f"<b>FPS:</b> <code>{s.get('fps')}</code>\n\n"
                f"Use the buttons below to modify your settings.")

    buttons = [
        [InlineKeyboardButton(flbl("Codec"), callback_data="user_set_enc_codec"),
         InlineKeyboardButton(flbl("CRF"), callback_data="user_set_enc_crf")],
        [InlineKeyboardButton(flbl("Preset"), callback_data="user_set_enc_preset"),
         InlineKeyboardButton(flbl("Audio Codec"), callback_data="user_set_enc_audio_codec")],
        [InlineKeyboardButton(flbl("Audio Bitrate"), callback_data="user_set_enc_audio_bitrate"),
         InlineKeyboardButton(flbl("Bit Depth"), callback_data="user_set_enc_bit_depth")],
        [InlineKeyboardButton(flbl("FPS"), callback_data="user_set_enc_fps"),
         InlineKeyboardButton(flbl("Reset Defaults"), callback_data="user_reset_enc_settings")],
        [InlineKeyboardButton(flbl("« Back"), callback_data="user_settings_back")]
    ]

    await edit_user_settings_reply(client, query, msg, InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^user_set_enc_codec$"))
async def user_set_enc_codec_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    msg = ftext("<blockquote><b>Select Video Codec</b></blockquote>")
    codecs = ["libx264", "libx265", "libsvtav1"]
    buttons = []
    for c in codecs:
        buttons.append([InlineKeyboardButton(flbl(c), callback_data=f"user_set_codec_{c}")])
    buttons.append([InlineKeyboardButton(flbl("« Back"), callback_data="user_enc_settings")])

    await edit_user_settings_reply(client, query, msg, InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^user_set_codec_(.*)$"))
async def user_set_codec_callback(client, query):
    codec = query.data.split("_", 3)[3]
    await client.mongodb.set_user_encode_setting(query.from_user.id, "codec", codec)
    await query.answer(f"Codec set to {codec}!")
    await user_enc_settings_cb(client, query)

@Client.on_callback_query(filters.regex("^user_set_enc_crf$"))
async def user_set_enc_crf_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    text = ftext("<blockquote><b>Send your preferred CRF value (e.g., 22).</b>\n\nLower is better quality, higher is smaller size. Typical: 18-28.</blockquote>")
    msg = await show_user_setting_prompt(client, query, text)

    try:
        res = await client.listen(chat_id=query.message.chat.id, user_id=user_id, filters=filters.text, timeout=60)
        await client.mongodb.set_user_encode_setting(user_id, "crf", res.text.strip())
        await res.reply(ftext(f"✅ **CRF set to:** `{res.text}`"))
    except ListenerTimeout:
        await msg.edit_text(ftext("❌ **Timeout!** No changes made."))

    await user_enc_settings_cb(client, query)

@Client.on_callback_query(filters.regex("^user_set_enc_preset$"))
async def user_set_enc_preset_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    msg = ftext("<blockquote><b>Select Encoder Preset</b></blockquote>")
    presets = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
    buttons = []
    for i in range(0, len(presets), 3):
        row = [InlineKeyboardButton(flbl(p), callback_data=f"user_set_preset_{p}") for p in presets[i:i+3]]
        buttons.append(row)
    buttons.append([InlineKeyboardButton(flbl("« Back"), callback_data="user_enc_settings")])

    await edit_user_settings_reply(client, query, msg, InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^user_set_preset_(.*)$"))
async def user_set_preset_callback(client, query):
    preset = query.data.split("_", 3)[3]
    await client.mongodb.set_user_encode_setting(query.from_user.id, "preset", preset)
    await query.answer(f"Preset set to {preset}!")
    await user_enc_settings_cb(client, query)

@Client.on_callback_query(filters.regex("^user_set_enc_audio_codec$"))
async def user_set_enc_audio_codec_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    msg = ftext("<blockquote><b>Select Audio Codec</b></blockquote>")
    codecs = ["aac", "libopus", "libmp3lame", "copy"]
    buttons = []
    for c in codecs:
        buttons.append([InlineKeyboardButton(flbl(c), callback_data=f"user_set_acodec_{c}")])
    buttons.append([InlineKeyboardButton(flbl("« Back"), callback_data="user_enc_settings")])

    await edit_user_settings_reply(client, query, msg, InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^user_set_acodec_(.*)$"))
async def user_set_acodec_callback(client, query):
    codec = query.data.split("_", 3)[3]
    await client.mongodb.set_user_encode_setting(query.from_user.id, "audio_codec", codec)
    await query.answer(f"Audio Codec set to {codec}!")
    await user_enc_settings_cb(client, query)

@Client.on_callback_query(filters.regex("^user_set_enc_audio_bitrate$"))
async def user_set_enc_audio_bitrate_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    text = ftext("<blockquote><b>Send your preferred Audio Bitrate (e.g., 96k, 128k).</b></blockquote>")
    msg = await show_user_setting_prompt(client, query, text)

    try:
        res = await client.listen(chat_id=query.message.chat.id, user_id=user_id, filters=filters.text, timeout=60)
        await client.mongodb.set_user_encode_setting(user_id, "audio_bitrate", res.text.strip())
        await res.reply(ftext(f"✅ **Audio Bitrate set to:** `{res.text}`"))
    except ListenerTimeout:
        await msg.edit_text(ftext("❌ **Timeout!** No changes made."))

    await user_enc_settings_cb(client, query)

@Client.on_callback_query(filters.regex("^user_set_enc_bit_depth$"))
async def user_set_enc_bit_depth_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    msg = ftext("<blockquote><b>Select Bit Depth</b></blockquote>")
    buttons = [
        [InlineKeyboardButton(flbl("8bit"), callback_data="user_set_bit_8bit"),
         InlineKeyboardButton(flbl("10bit"), callback_data="user_set_bit_10bit")],
        [InlineKeyboardButton(flbl("« Back"), callback_data="user_enc_settings")]
    ]

    await edit_user_settings_reply(client, query, msg, InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^user_set_bit_(.*)$"))
async def user_set_bit_callback(client, query):
    bit = query.data.split("_", 3)[3]
    await client.mongodb.set_user_encode_setting(query.from_user.id, "bit_depth", bit)
    await query.answer(f"Bit Depth set to {bit}!")
    await user_enc_settings_cb(client, query)

@Client.on_callback_query(filters.regex("^user_set_enc_fps$"))
async def user_set_enc_fps_cb(client, query):
    user_id = query.from_user.id
    await query.answer()

    text = ftext("<blockquote><b>Send your preferred FPS (12-60).</b></blockquote>")
    msg = await show_user_setting_prompt(client, query, text)

    try:
        res = await client.listen(chat_id=query.message.chat.id, user_id=user_id, filters=filters.text, timeout=60)
        val = res.text.strip()
        if val.isdigit() and 12 <= int(val) <= 60:
            await client.mongodb.set_user_encode_setting(user_id, "fps", val)
            await res.reply(ftext(f"✅ **FPS set to:** `{val}`"))
        else:
            await res.reply(ftext("❌ **Invalid FPS!** Use a value between 12 and 60."))
    except ListenerTimeout:
        await msg.edit_text(ftext("❌ **Timeout!** No changes made."))

    await user_enc_settings_cb(client, query)

@Client.on_callback_query(filters.regex("^user_reset_enc_settings$"))
async def user_reset_enc_settings_cb(client, query):
    await client.mongodb.set_user_setting(query.from_user.id, "encode_settings", {})
    await query.answer("✅ Encoding settings reset to defaults!", show_alert=True)
    await user_enc_settings_cb(client, query)

# --- Command Handlers (Per-user) ---

@Client.on_message(filters.command("crf") & auth_filter)
async def set_user_crf(client, message):
    if len(message.command) < 2:
        return await message.reply(ftext("<b>Usage:</b> /crf <value>"))
    val = message.command[1]
    await client.mongodb.set_user_encode_setting(message.from_user.id, "crf", val)
    await message.reply(ftext(f"✅ <b>CRF set to:</b> <code>{val}</code>"))

@Client.on_message(filters.command("codec") & auth_filter)
async def set_user_codec(client, message):
    if len(message.command) < 2:
        return await message.reply(ftext("<b>Usage:</b> /codec <name>"))
    val = message.command[1]
    await client.mongodb.set_user_encode_setting(message.from_user.id, "codec", val)
    await message.reply(ftext(f"✅ <b>Codec set to:</b> <code>{val}</code>"))

@Client.on_message(filters.command("preset") & auth_filter)
async def set_user_preset(client, message):
    if len(message.command) < 2:
        return await message.reply(ftext("<b>Usage:</b> /preset <name>"))
    val = message.command[1]
    await client.mongodb.set_user_encode_setting(message.from_user.id, "preset", val)
    await message.reply(ftext(f"✅ <b>Preset set to:</b> <code>{val}</code>"))

@Client.on_message(filters.command("audiocodec") & auth_filter)
async def set_user_audio_codec(client, message):
    if len(message.command) < 2:
        return await message.reply(ftext("<b>Usage:</b> /audiocodec <codec>"))
    val = message.command[1]
    await client.mongodb.set_user_encode_setting(message.from_user.id, "audio_codec", val)
    await message.reply(ftext(f"✅ <b>Audio Codec set to:</b> <code>{val}</code>"))

@Client.on_message(filters.command("audio") & auth_filter)
async def set_user_audio_bitrate(client, message):
    if len(message.command) < 2:
        return await message.reply(ftext("<b>Usage:</b> /audio <bitrate> (e.g. 96k)"))
    val = message.command[1]
    await client.mongodb.set_user_encode_setting(message.from_user.id, "audio_bitrate", val)
    await message.reply(ftext(f"✅ <b>Audio Bitrate set to:</b> <code>{val}</code>"))

@Client.on_message(filters.command("bit") & auth_filter)
async def set_user_bit_depth(client, message):
    if len(message.command) < 2:
        curr = (await client.mongodb.get_user_encode_settings(message.from_user.id)).get('bit_depth', '10bit')
        val = "8bit" if curr == "10bit" else "10bit"
    else:
        val = message.command[1]
        if val not in ["8bit", "10bit"]:
             return await message.reply(ftext("<b>Invalid Bit Depth!</b> Use 8bit or 10bit."))
    await client.mongodb.set_user_encode_setting(message.from_user.id, "bit_depth", val)
    await message.reply(ftext(f"✅ <b>Bit Depth set to:</b> <code>{val}</code>"))

@Client.on_message(filters.command("fps") & auth_filter)
async def set_user_fps(client, message):
    if len(message.command) < 2:
        return await message.reply(ftext("<b>Usage:</b> /fps <12-60>"))
    val = message.command[1]
    if val.isdigit() and 12 <= int(val) <= 60:
        await client.mongodb.set_user_encode_setting(message.from_user.id, "fps", val)
        await message.reply(ftext(f"✅ <b>FPS set to:</b> <code>{val}</code>"))
    else:
        await message.reply(ftext("❌ **Invalid FPS!** Use a value between 12 and 60."))

@Client.on_message(filters.command("resetsettings") & auth_filter)
async def reset_user_settings(client, message):
    await client.mongodb.set_user_setting(message.from_user.id, "encode_settings", {})
    await message.reply(ftext("✅ <b>Encoding settings reset to defaults!</b>"))
