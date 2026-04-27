from helper.utils import auth_filter
from pyrogram import Client, filters
from pyrogram.types import Message
from helper.helper_func import ftext

@Client.on_message(filters.command("id") & auth_filter)
async def id_handler(client: Client, message: Message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    chat_id = message.chat.id

    response = ""

    if message.reply_to_message:
        replied = message.reply_to_message
        replied_user_id = replied.from_user.id if replied.from_user else "None"

        if replied.forward_from_chat:
            fwd_chat_id = replied.forward_from_chat.id
            response = (
                f"➥ {ftext('Your User ID')}: <code>{user_id}</code>\n"
                f"➥ {ftext('Forwarded Chat ID')}: <code>{fwd_chat_id}</code>"
            )
        elif replied.forward_from:
            fwd_user_id = replied.forward_from.id
            response = (
                f"➥ {ftext('Your User ID')}: <code>{user_id}</code>\n"
                f"➥ {ftext('Replied User ID')}: <code>{replied_user_id}</code>\n"
                f"➥ {ftext('Forwarded User ID')}: <code>{fwd_user_id}</code>\n"
                f"➥ {ftext('Chat ID')}: <code>{chat_id}</code>"
            )
        else:
            response = (
                f"➥ {ftext('Your User ID')}: <code>{user_id}</code>\n"
                f"➥ {ftext('Replied User ID')}: <code>{replied_user_id}</code>\n"
                f"➥ {ftext('Chat ID')}: <code>{chat_id}</code>"
            )
    elif len(message.command) > 1:
        arg = message.command[1]
        try:
            if arg.startswith("@"):
                target_user = await client.get_users(arg)
            else:
                target_user = await client.get_users(int(arg))

            target_user_id = target_user.id
            response = (
                f"➥ {ftext('Your User ID')}: <code>{user_id}</code>\n"
                f"➥ {ftext('Target User ID')} ({arg}): <code>{target_user_id}</code>\n"
                f"➥ {ftext('Chat ID')}: <code>{chat_id}</code>"
            )
        except Exception as e:
             response = ftext(f"Error: {e}")
    else:
        response = (
            f"➥ {ftext('Your User ID')}: <code>{user_id}</code>\n"
            f"➥ {ftext('Chat ID')}: <code>{chat_id}</code>"
        )

    await message.reply(ftext(response))
