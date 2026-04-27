from helper.utils import auth_filter, auth_user, is_video
from pyrogram import filters, Client
from pyrogram.types import Message
from helper.helper_func import ftext


@Client.on_message(
    (filters.private | auth_filter) &
    ~filters.regex(r"^/")
)
async def channel_post(client: Client, message: Message):
    if message.media_group_id:
        return
    user_id = message.from_user.id if message.from_user else message.chat.id
    if not await auth_user(None, client, message):
        return await message.reply(ftext(getattr(client, "reply_text", "Access Denied")))

    # Handle Encode Mode (Prioritize User's Auto Encode)
    if is_video(message):
        auto_encode = await client.mongodb.get_user_setting(user_id, "auto_encode", False)
        if auto_encode:
            from plugins.encode import start_encoding
            quality = await client.mongodb.get_user_setting(user_id, "encode_quality")
            if not quality:
                quality = getattr(client, "encode_quality", "all")
            return await start_encoding(client, message, quality, user_id=user_id)

    bot_mode = getattr(client, "bot_mode", "auto_encode")

    # Handle Auto Rename Mode
    if bot_mode == "auto_rename" and (message.document or message.video or message.audio):
        from plugins.auto_rename import process_file
        return await process_file(client, message, user_id)

    # Handle Manual Rename Mode
    if bot_mode == "manual_rename" and (message.document or message.video or message.audio):
        from plugins.manual_rename import start_manual_rename
        return await start_manual_rename(client, message)


