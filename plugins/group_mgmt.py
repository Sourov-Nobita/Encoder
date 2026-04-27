from helper.utils import auth_filter
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPrivileges
from helper.helper_func import ftext, flbl, is_admin, get_readable_time, force_sub
import time

@Client.on_message(filters.command("authorize") & auth_filter)
@force_sub
async def authorize_command(client: Client, message: Message):
    if not message.from_user or message.from_user.id not in client.admins:
        return await message.reply(ftext(getattr(client, 'reply_text', 'This command is only for admins.')))

    await client.mongodb.authorize_group(message.chat.id)
    await message.reply(ftext("This group has been authorized for management features"))

@Client.on_message(filters.command("unauthorize") & auth_filter)
@force_sub
async def unauthorize_command(client: Client, message: Message):
    if not message.from_user or message.from_user.id not in client.admins:
        return await message.reply(ftext(getattr(client, 'reply_text', 'This command is only for admins.')))

    await client.mongodb.unauthorize_group(message.chat.id)
    await message.reply(ftext("This group has been unauthorized"))

@Client.on_message(filters.command("ban") & auth_filter)
@force_sub
async def ban_command(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if not message.reply_to_message:
        await message.reply(ftext("Reply to a user to ban them"))
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    try:
        await message.chat.ban_member(user_id=user_id)
        await message.reply(ftext(f"User {user_name} ({user_id}) has been banned"))
    except Exception as e:
        await message.reply(ftext(f"Failed to ban user: {e}"))

@Client.on_message(filters.command("kick") & auth_filter)
@force_sub
async def kick_command(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if not message.reply_to_message:
        await message.reply(ftext("Reply to a user to kick them"))
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    try:
        await message.chat.ban_member(user_id=user_id)
        await message.chat.unban_member(user_id=user_id)
        await message.reply(ftext(f"User {user_name} ({user_id}) has been kicked"))
    except Exception as e:
        await message.reply(ftext(f"Failed to kick user: {e}"))

@Client.on_message(filters.command("warn") & auth_filter)
@force_sub
async def warn_command(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if not message.reply_to_message:
        await message.reply(ftext("Reply to a user to warn them"))
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    count = await client.mongodb.add_warn(user_id, message.chat.id)

    if count >= 3:
        try:
            await message.chat.ban_member(user_id=user_id)
            await client.mongodb.reset_warns(user_id, message.chat.id)
            await message.reply(ftext(f"User {user_name} ({user_id}) has been banned for reaching 3 warnings"))
        except Exception as e:
            await message.reply(ftext(f"Failed to ban user after 3 warns: {e}"))
    else:
        await message.reply(ftext(f"User {user_name} ({user_id}) has been warned ({count}/3)"))

@Client.on_message(filters.command("rem_warn") & auth_filter)
@force_sub
async def rem_warn_command(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if not message.reply_to_message:
        await message.reply(ftext("Reply to a user to remove their warning"))
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name

    current_warns = await client.mongodb.get_warns(user_id, message.chat.id)
    if current_warns > 0:
        await client.mongodb.reset_warns(user_id, message.chat.id)
        await message.reply(ftext(f"Warnings for {user_name} ({user_id}) have been removed"))
    else:
        await message.reply(ftext(f"User {user_name} has no warnings"))

@Client.on_message(filters.command("promote") & auth_filter)
@force_sub
async def promote_command(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if not message.reply_to_message:
        await message.reply(ftext("Reply to a user to promote them"))
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            privileges=ChatPrivileges(
                can_change_info=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_restrict_members=True,
                can_pin_messages=True,
                can_promote_members=False
            )
        )
        await message.reply(ftext(f"User {user_name} ({user_id}) has been promoted to admin"))
    except Exception as e:
        await message.reply(ftext(f"Failed to promote user: {e}"))

@Client.on_message(filters.command("demote") & auth_filter)
@force_sub
async def demote_command(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return

    if not message.reply_to_message:
        await message.reply(ftext("Reply to a user to demote them"))
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            privileges=ChatPrivileges(
                can_change_info=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False
            )
        )
        await message.reply(ftext(f"User {user_name} ({user_id}) has been demoted"))
    except Exception as e:
        await message.reply(ftext(f"Failed to demote user: {e}"))

@Client.on_message(filters.command("pinned") & auth_filter)
@force_sub
async def pinned_command(client: Client, message: Message):
    chat = await client.get_chat(message.chat.id)
    if chat.pinned_message:
        await message.reply(ftext("The current pinned message is here") + f": {chat.pinned_message.link}")
    else:
        await message.reply(ftext("There is no pinned message in this chat"))

@Client.on_message(filters.command("unpin") & auth_filter)
@force_sub
async def unpin_command(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return
    try:
        if message.reply_to_message:
            await client.unpin_chat_message(message.chat.id, message.reply_to_message.id)
            await message.reply(ftext("Message unpinned"))
        else:
            await client.unpin_chat_message(message.chat.id)
            await message.reply(ftext("Last pinned message unpinned"))
    except Exception as e:
        await message.reply(ftext(f"Failed to unpin: {e}"))

@Client.on_message(filters.command("pin") & auth_filter)
@force_sub
async def pin_command(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        await message.reply(ftext("Reply to a message to pin it"))
        return

    disable_notification = True
    if "loud" in (message.text or "").lower() or "notify" in (message.text or "").lower():
        disable_notification = False

    try:
        await client.pin_chat_message(message.chat.id, message.reply_to_message.id, disable_notification=disable_notification)
        await message.reply(ftext("Message pinned"))
    except Exception as e:
        await message.reply(ftext(f"Failed to pin: {e}"))

@Client.on_message(filters.command("approve") & auth_filter)
@force_sub
async def approve_command(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        await message.reply(ftext("Reply to a user to approve them"))
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    await client.mongodb.approve_user(message.chat.id, user_id)
    await message.reply(ftext(f"{user_name} has been approved in this chat"))

@Client.on_message(filters.command("unapprove") & auth_filter)
@force_sub
async def unapprove_command(client: Client, message: Message):
    if not message.from_user or not await is_admin(client, message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        await message.reply(ftext("Reply to a user to unapprove them"))
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    await client.mongodb.unapprove_user(message.chat.id, user_id)
    await message.reply(ftext(f"{user_name} is no longer approved in this chat"))

@Client.on_message(filters.command("afk") & auth_filter)
@force_sub
async def afk_command(client: Client, message: Message):
    if not message.from_user:
        return

    reason = message.text.split(None, 1)[1] if len(message.command) > 1 else "No reason provided"
    await client.mongodb.set_afk(message.from_user.id, reason, time.time())
    await message.reply(ftext(f"{message.from_user.first_name} is now AFK") + f"!\n{ftext('Reason')}: {reason}")

@Client.on_message(filters.group & ~filters.bot, group=1)
async def afk_handler(client: Client, message: Message):

    processed_users = set()

    if message.entities:
        for entity in message.entities:
            user_id = None
            first_name = "User"
            if entity.type == entity.type.MENTION:
                username = message.text[entity.offset:entity.offset+entity.length].replace("@", "")
                try:
                    user = await client.get_users(username)
                    user_id = user.id
                    first_name = user.first_name
                except Exception:
                    pass
            elif entity.type == entity.type.TEXT_MENTION:
                user_id = entity.user.id
                first_name = entity.user.first_name

            if user_id and user_id not in processed_users:
                processed_users.add(user_id)
                afk_data = await client.mongodb.get_afk(user_id)
                if afk_data:
                    reason = afk_data['reason']
                    readable_time = get_readable_time(int(time.time() - afk_data['time']))
                    await message.reply(ftext(f"{first_name} is AFK since {readable_time}") + f"!\n{ftext('Reason')}: {reason}")

    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user
        if replied_user.id not in processed_users:
            processed_users.add(replied_user.id)
            afk_data = await client.mongodb.get_afk(replied_user.id)
            if afk_data:
                reason = afk_data['reason']
                readable_time = get_readable_time(int(time.time() - afk_data['time']))
                await message.reply(ftext(f"{replied_user.first_name} is AFK since {readable_time}") + f"!\n{ftext('Reason')}: {reason}")

    if not message.from_user:
        return

    afk_data = await client.mongodb.get_afk(message.from_user.id)
    if afk_data:
        await client.mongodb.remove_afk(message.from_user.id)
        readable_time = get_readable_time(int(time.time() - afk_data['time']))
        await message.reply(ftext(f"Welcome back {message.from_user.first_name}! I have removed your AFK status. You were AFK for {readable_time}"))
