from helper.utils import auth_filter
from pyrogram import Client, filters
from pyrogram.types import Message
from helper.helper_func import ftext, flbl
import logging

@Client.on_message(filters.command("info") & auth_filter)
async def info_command(client: Client, message: Message):
    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        arg = message.command[1]
        try:
            if arg.startswith("@"):
                target_user = await client.get_users(arg)
            else:
                target_user = await client.get_users(int(arg))
        except Exception as e:
            await message.reply(ftext(f"Error: {e}"))
            return
    else:
        target_user = message.from_user

    if not message.from_user and not target_user:
        return

    if not target_user:
        await message.reply(ftext("Could not find user"))
        return

    user_id = target_user.id
    first_name = target_user.first_name
    last_name = target_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = f"@{target_user.username}" if target_user.username else "None"

    dc_id = getattr(target_user, "dc_id", "Unavailable")
    language = target_user.language_code or "en"
    premium = "Yes" if target_user.is_premium else "No"
    account_type = "Bot" if target_user.is_bot else "User"

    has_profile_pic = "No"
    if target_user.photo:
        has_profile_pic = "Yes"

    info_text = (
        f"❐ {ftext('User Information')} :-\n\n"
        f"➥ {ftext('User ID')}: <code>{user_id}</code>\n"
        f"➥ {ftext('Data Center')}: <code>{dc_id}</code>\n"
        f"➥ {ftext('Name')}: {full_name}\n"
        f"➥ {ftext('Username')}: {username}\n"
        f"➥ {ftext('Language')}: {language}\n"
        f"➥ {ftext('Premium')}: {premium}\n"
        f"➥ {ftext('Account Type')}: {account_type}\n"
        f"➥ {ftext('Profile Picture')}: {has_profile_pic}\n"
    )

    if has_profile_pic == "Yes":
        try:
            await message.reply_photo(
                photo=target_user.photo.big_file_id,
                caption=ftext(info_text)
            )
        except Exception as e:
            logging.error(f"Error sending photo for {user_id}: {e}")
            await message.reply(ftext(info_text))
    else:
        await message.reply(ftext(info_text))
