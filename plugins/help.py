from helper.utils import auth_filter
from helper.helper_func import ftext, flbl
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

@Client.on_message(filters.command('help'))
async def help_command(client: Client, message: Message):
    """Handles the /help command by sending a new message."""
    await send_help_message(client, message)

@Client.on_callback_query(filters.regex('^help$'))
async def help_callback(client: Client, query: CallbackQuery):
    """Handles the 'Help' button callback by editing the message."""
    await query.answer()
    await send_help_message(client, query.message, is_callback=True, user=query.from_user)

async def send_help_message(client: Client, message: Message, is_callback=False, user=None):
    """A helper function to construct and send/edit the help message."""
    from_user = user if user else message.from_user

    help_text_template = client.messages.get('HELP', 'No help message configured.')
    photo = client.messages.get('HELP_PHOTO', 'https://graph.org/file/60b18716404fc1bb7a7d8-c85717ceefd738c2f7.jpg')
    support_url = client.messages.get('SUPPORT_GRP')
    owner_url = client.messages.get('OWNER_URL')
    network_url = client.messages.get('NETWORK_URL')

    buttons = []
    if True: # Show for all
        if support_url:
            buttons.append([InlineKeyboardButton(flbl("Support Chat Group"), url=support_url)])

        row2 = []
        if owner_url:
            row2.append(InlineKeyboardButton(flbl("Owner"), url=owner_url))
        if network_url:
            row2.append(InlineKeyboardButton(flbl("Network"), url=network_url))
        if row2:
            buttons.append(row2)
    
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    final_text = f"<b>⁉️ Hello {from_user.mention} ~\n\n</b>"
    final_text += help_text_template.format(
        first=from_user.first_name,
        last=from_user.last_name,
        username=f'@{from_user.username}' if from_user.username else 'None',
        mention=from_user.mention,
        id=from_user.id
    )
    final_text += "\n\n<b><i>◈ Still have doubts, contact below persons/group as per your need !</i></b>"
    final_text = ftext(final_text)

    if is_callback:
        has_photo = bool(message.photo)
        wants_photo = bool(photo)

        if wants_photo and not has_photo:
            await message.delete()
            await client.send_photo(chat_id=message.chat.id, photo=photo, caption=final_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        elif wants_photo and has_photo:
            await message.edit_caption(caption=final_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        elif not wants_photo and has_photo:
            await message.delete()
            await client.send_message(chat_id=message.chat.id, text=final_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await message.edit_text(text=final_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        if photo:
            await message.reply_photo(photo=photo, caption=final_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(text=final_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
