from helper.utils import auth_filter
from helper.helper_func import font_shaper, flbl, ftext
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from helper.custom_listen import ListenerTimeout
from helper.helper_func import is_bot_admin

async def fsub(client, query):
    """
    Displays the Force Subscribe management menu with detailed status for each channel.
    """
    channel_list_text = ""
    if client.fsub_dict:
        channel_lines = []
        for channel_id, data in client.fsub_dict.items():
            name = data[0]
            is_request = data[2]
            timer = data[3]
            
            request_text = "✓ REQUEST" if is_request else "✗ DIRECT"
            timer_text = f"{timer}m" if timer > 0 else "☠ PERMANENT"
            
            line = f"• <b>{name}</b>\n(<code>{channel_id}</code>) - <b>{request_text}</b> - <b>TIMER:</b> {timer_text}"
            channel_lines.append(line)

        channel_list_text = "\n\n".join(channel_lines)
    else:
        channel_list_text = ">> <i>None configured.</i>"

    msg = ftext(f"""<blockquote><b>✧ FORCE SUBSCRIPTION SETTINGS</b></blockquote>
<b>>> CONFIGURED CHANNELS:</b>
{channel_list_text}

<i>Use the appropriate button below to add or remove a force subscribe channel!</i>
""")
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(flbl('Add Channel'), 'add_fsub'), InlineKeyboardButton(flbl('Remove Channel'), 'rm_fsub')],
        [InlineKeyboardButton(flbl('« Back'), 'settings_pg1')]
    ])
    await query.message.edit_text(msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

@Client.on_callback_query(filters.regex('^add_fsub$'))
async def add_fsub(client: Client, query: CallbackQuery):
    """
    Handles adding a new channel to the force subscribe list and updates the live dictionary.
    """
    await query.answer()
    prompt_message = await query.message.edit_text(
        ftext("""<blockquote><b>➕ ADD A FORCE SUB CHANNEL</b></blockquote>
Please send the channel details in this format:
<code>Channel_ID Request_Enabled Timer_in_Minutes</code>

<b>Example:</b> <code>-100123456789 yes 5</code>
>> <code>-100...</code> is the Channel ID.
>> <code>yes</code> enables request-to-join links. Use <code>no</code> for public invite links.
>> <code>5</code> means the link will expire after 5 minutes. Use <code>0</code> for a non-expiring link.
"""), parse_mode=ParseMode.HTML)
    
    try:
        response_message = await client.listen(chat_id=query.from_user.id, filters=filters.text, timeout=90)
        
        channel_info = response_message.text.split()
        if len(channel_info) != 3:
            return await response_message.reply(ftext("<b>Invalid format.</b> Please provide all three values as requested."), parse_mode=ParseMode.HTML)
        
        channel_id_str, request_str, timer_str = channel_info
        channel_id = int(channel_id_str)
        
        if any(channel[0] == channel_id for channel in client.fsub):
            return await response_message.reply(ftext("<b>This channel ID already exists in the force sub list.</b>"), parse_mode=ParseMode.HTML)
        
        val, res = await is_bot_admin(client, channel_id)
        if not val:
            return await response_message.reply(ftext(f"<b>Error:</b> <code>{res}</code>"), parse_mode=ParseMode.HTML)
        
        request = request_str.lower() in ('true', 'on', 'yes')
        timer = int(timer_str)

        client.fsub.append([channel_id, request, timer])
        
        chat = await client.get_chat(channel_id)
        name = chat.title
        link = None
        if timer <= 0:
            try:
                if not request and chat.invite_link:
                    link = chat.invite_link
                else:
                    invite = await client.create_chat_invite_link(channel_id, creates_join_request=request)
                    link = invite.invite_link
            except Exception as e:
                client.LOGGER(__name__, client.name).warning(f"Couldn't create invite link for {channel_id}: {e}")
        
        client.fsub_dict[channel_id] = [name, link, request, timer]
        
        await client.mongodb.save_settings(client.name, client.get_current_settings())
        await response_message.reply(ftext(f"✅ Channel <b>{name}</b> (<code>{channel_id}</code>) has been added successfully."), parse_mode=ParseMode.HTML)
        
    except ListenerTimeout:
        await prompt_message.edit_text(ftext("<b>Timeout! No changes were made.</b>"))
    except Exception as e:
        await query.message.reply(ftext(f"<b>An error occurred:</b> <code>{e}</code>"), parse_mode=ParseMode.HTML)
    
    await fsub(client, query)

@Client.on_callback_query(filters.regex('^rm_fsub$'))
async def rm_fsub(client: Client, query: CallbackQuery):
    await query.answer()
    prompt_message = await query.message.edit_text(
        ftext("<blockquote><b>➖ Remove a Force Sub Channel</b></blockquote>\nPlease send the Channel ID of the channel you want to remove."),
        parse_mode=ParseMode.HTML
    )
    try:
        response_message = await client.listen(chat_id=query.from_user.id, filters=filters.text, timeout=60)
        channel_id = int(response_message.text)
        
        if not any(channel[0] == channel_id for channel in client.fsub):
            return await response_message.reply(ftext("<b>This channel ID is not in the force sub list!</b>"), parse_mode=ParseMode.HTML)
        
        client.fsub = [channel for channel in client.fsub if channel[0] != channel_id]
        
        removed_channel = client.fsub_dict.pop(channel_id, None)
        
        await client.mongodb.save_settings(client.name, client.get_current_settings())
        
        channel_name = f"<b>{removed_channel[0]}</b> " if removed_channel else ""
        await response_message.reply(ftext(f"✅ Channel {channel_name}(<code>{channel_id}</code>) has been removed."), parse_mode=ParseMode.HTML)
        
    except ListenerTimeout:
        await prompt_message.edit_text(ftext("<b>Timeout! No changes were made.</b>"))
    except Exception as e:
        await query.message.reply(ftext(f"<b>An error occurred:</b> <code>{e}</code>"), parse_mode=ParseMode.HTML)
        
    await fsub(client, query)




