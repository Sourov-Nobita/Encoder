from helper.utils import auth_filter
from helper.helper_func import font_shaper, ftext, flbl, graceful_restart
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from config import OWNER_ID
import time
import os
import sys
import psutil
import shutil

async def admins(client, query):
    if query.from_user.id not in client.admins:
        return await query.answer(ftext('This can only be used by admins.'))
    msg = ftext(f"""<blockquote>**Admin Settings:**</blockquote>
**Admin User IDs:** {", ".join(f"`{a}`" for a in client.admins)}

Use the appropriate button below to add or remove an admin based on your needs!""")

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(flbl('Add Admin'), 'add_admin'), InlineKeyboardButton(flbl('Remove Admin'), 'rm_admin')],
        [InlineKeyboardButton(flbl('« Back'), 'settings_pg1')]
    ])
    await query.message.edit_text(msg, reply_markup=reply_markup)
    return

@Client.on_message(filters.command("usage") & auth_filter)
async def usage_cmd(client: Client, message: Message):
    if not message.from_user or message.from_user.id not in client.admins:
        return await message.reply(ftext(getattr(client, 'reply_text', 'This command is only for admins.')))
        
    reply = await message.reply(ftext("Extracting all Usage!!"))

    total, used, free = shutil.disk_usage("/")
    total_gb, used_gb, free_gb = total / (1024**3), used / (1024**3), free / (1024**3)

    ram = psutil.virtual_memory()
    total_ram, used_ram, free_ram = ram.total / (1024**3), ram.used / (1024**3), ram.available / (1024**3)

    swap = psutil.swap_memory()
    total_swap, used_swap, free_swap = swap.total / (1024**3), swap.used / (1024**3), swap.free / (1024**3)

    try:
        net_io = psutil.net_io_counters()
        bytes_sent, bytes_recv = net_io.bytes_sent / (1024**2), net_io.bytes_recv / (1024**2)
        net_msg = f"**📡 Network:** `↑ {bytes_sent:.2f} MB` | `↓ {bytes_recv:.2f} MB`\n"
    except (PermissionError, AttributeError):
        net_msg = ""

    process = psutil.Process()
    bot_cpu, bot_mem = process.cpu_percent(interval=1), process.memory_info().rss / (1024**2)

    msg = ftext(
        f"<blockquote>**📊 System Usage Stats:**</blockquote>\n"
        f"**💾 Disk:** `{used_gb:.2f} GB / {total_gb:.2f} GB`\n"
        f"**🖥 RAM:** `{used_ram:.2f} GB / {total_ram:.2f} GB` ({ram.percent}%)\n"
        f"**🔄 Swap:** `{used_swap:.2f} GB / {total_swap:.2f} GB` ({swap.percent}%)\n"
        f"**⚡ CPU:** `{psutil.cpu_percent(interval=1):.2f}%`\n"
        f"{net_msg}"
        f"**🤖 Bot:** `CPU {bot_cpu:.2f}%` | `MEM {bot_mem:.2f} MB`"
    )

    await reply.edit_text(msg)

@Client.on_message(filters.command("restart") & auth_filter)
async def restart_bot(client: Client, message: Message):
    if not message.from_user or message.from_user.id not in client.admins:
        return await message.reply(ftext(getattr(client, 'reply_text', 'This command is only for admins.')))

    await graceful_restart(client, message)
    
@Client.on_message(filters.command("reset") & auth_filter)
async def reset_bot_settings(client: Client, message: Message):
    if not message.from_user or message.from_user.id not in client.admins:
        return await message.reply(ftext(getattr(client, 'reply_text', 'This command is only for admins.')))

    """
    Deletes cosmetic and basic configuration settings from the database,
    forcing a reload from setup.json while preserving important data.
    """
    await message.reply_text(
        ftext("⚠️ **Confirm Configuration Reset**\n\n"
        "This will reset settings like **messages, photos, admins, and FSub channels** to their original values from `setup.json`.\n\n"
        "✅ **The Following Data will be Preserved:**\n"
        "• Total Users & Premium Users\n"
        "• All Generated Links\n"
        "• Shortener API Key\n"
        "• **Auto-Approval Channel List**\n\n"
        "The bot will restart to apply the changes."),
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(flbl("Yes"), callback_data="confirm_safe_reset"),
                InlineKeyboardButton(flbl("Cancel"), callback_data="cancel_reset")
            ]]
        )
    )

@Client.on_callback_query(filters.regex("^confirm_safe_reset$"))
async def confirm_safe_reset_cb(client: Client, query: CallbackQuery):
    if query.from_user.id not in client.admins:
        return await query.answer(ftext("This is not for you!"), show_alert=True)
    
    await query.message.edit_text(ftext("🔥 **Resetting Configuration...**\n\nDeleting global and session settings. The bot will restart shortly."))
    
    try:
        # Delete only global and session-specific settings
        await client.mongodb.database_obj["bot_settings"].delete_many({"_id": {"$in": ["global_config", client.name]}})
        client.LOGGER(__name__, client.name).info(f"Global config and session {client.name} settings deleted by owner for config reset.")
            
    except Exception as e:
        client.LOGGER(__name__, client.name).error(f"Failed to drop bot_settings during reset: {e}")
        return await query.message.edit_text(ftext(f"❌ **Error:** Could not delete settings from the database.\n\n`{e}`"))
        
    await query.message.edit_text(ftext("✅ **Configuration settings deleted.** Restarting now..."))
    await graceful_restart(client, query)

@Client.on_callback_query(filters.regex("^cancel_reset$"))
async def cancel_reset_cb(client: Client, query: CallbackQuery):
    if query.from_user.id not in client.admins:
        return await query.answer(ftext("This is not for you!"), show_alert=True)
    await query.message.edit_text(ftext("**🥀 Reset cancelled.**"))

@Client.on_callback_query(filters.regex("^add_admin$"))
async def add_new_admins(client: Client, query: CallbackQuery):
    await query.answer()
    if not query.from_user.id in client.admins:
        return await client.send_message(query.from_user.id, ftext(getattr(client, 'reply_text', 'This command is only for admins.')))
    try:
        ids_msg = await client.ask(query.from_user.id, ftext("Send user ids seperated by a space in the next 60 seconds!\nEg: `838278682 83622928 82789928`"), filters=filters.text, timeout=60)
        ids = ids_msg.text.split()
        
        for identifier in ids:
            if int(identifier) not in client.admins:
                client.admins.append(int(identifier))
        await client.mongodb.save_settings(client.name, client.get_current_settings())
        await admins(client, query)
        await ids_msg.reply(ftext(f"{len(ids)} admin {'id' if len(ids)==1 else 'ids'} have been promoted!!"))
    except Exception as e:
        await ids_msg.reply(ftext(f"Error: {e}"))
    
@Client.on_callback_query(filters.regex("^rm_admin$"))
async def remove_admins(client: Client, query: CallbackQuery):
    await query.answer()
    if not query.from_user.id in client.admins:
        return await client.send_message(query.from_user.id, ftext(getattr(client, 'reply_text', 'This command is only for admins.')))
    try:
        ids_msg = await client.ask(query.from_user.id, ftext("Send user ids seperated by a space in the next 60 seconds!\nEg: `838278682 83622928 82789928`"), filters=filters.text, timeout=60)
        ids = ids_msg.text.split()
        
        for identifier in ids:
            if int(identifier) == client.owner:
                await client.send_message(query.from_user.id, ftext("You cannot remove the owner from the admin list!"))
                continue
            if int(identifier) in client.admins:
                client.admins.remove(int(identifier))
        await client.mongodb.save_settings(client.name, client.get_current_settings())
        await admins(client, query)
        await ids_msg.reply(ftext(f"{len(ids)} admin {'id' if len(ids)==1 else 'ids'} have been removed!!"))
    except Exception as e:
        await ids_msg.reply(ftext(f"Error: {e}"))
