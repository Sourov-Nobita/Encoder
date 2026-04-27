from helper.utils import auth_filter
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from helper.custom_listen import ListenerTimeout
from helper.helper_func import font_shaper, flbl, ftext

async def texts(client, query):
    msg = ftext(f"""<blockquote><b>✧ Text Configuration</b></blockquote>
<b>>> Start Message :</b>
<pre>{client.messages.get('START', 'Empty')}</pre>
<b>>> FSub Message :</b>
<pre>{client.messages.get('FSUB', 'Empty')}</pre>
<b>>> About Message :</b>
<pre>{client.messages.get('ABOUT', 'Empty')}</pre>
<b>>> Help Message :</b>
<pre>{client.messages.get('HELP', 'Empty')}</pre>
<b>>> Reply Message :</b>
<pre>{client.reply_text}</pre>

<b>>> Support Group :</b> <code>{client.messages.get('SUPPORT_GRP', 'Not Set')}</code>
<b>>> Owner Url :</b> <code>{client.messages.get('OWNER_URL', 'Not Set')}</code>
<b>>> Network Url :</b> <code>{client.messages.get('NETWORK_URL', 'Not Set')}</code>""")

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(flbl('Start Text'), 'start_txt'), InlineKeyboardButton(flbl('FSub Text'), 'fsub_txt')],
        [InlineKeyboardButton(flbl('Reply Text'), 'reply_txt'), InlineKeyboardButton(flbl('About Text'), 'about_txt')],
        [InlineKeyboardButton(flbl('Help Text'), 'help_txt')],
        [InlineKeyboardButton(flbl('Support Url'), 'support_url'), InlineKeyboardButton(flbl('Owner Url'), 'owner_url')],
        [InlineKeyboardButton(flbl('Network Url'), 'network_url')],
        [InlineKeyboardButton(flbl('« Back'), 'settings_pg3')]
    ])
    await query.message.edit_text(msg, reply_markup=reply_markup)

async def handle_text_update(client, query, key, prompt):
    await query.answer()
    try:
        ask_text = await client.ask(query.from_user.id, prompt, filters=filters.text, timeout=60)
        text = ask_text.text
        if text.lower() == 'cancel':
            await ask_text.reply(ftext("🚫 Action cancelled. No changes were made."))
            await texts(client, query)
            return

        if key == 'REPLY':
            client.reply_text = text
        else:
            client.messages[key] = text
        
        await client.mongodb.save_settings(client.name, client.get_current_settings())
        await ask_text.reply(ftext(f"✅ **{key.replace('_', ' ').title()}** has been updated successfully!"))
        await texts(client, query)
    except ListenerTimeout:
        await query.message.reply(ftext("**Timeout! No changes were made.**"))
    except Exception as e:
        client.LOGGER(__name__, client.name).error(e)
        await query.message.reply(ftext(f"An error occurred: {e}"))

@Client.on_callback_query(filters.regex("^start_txt$"))
async def start_txt(client: Client, query: CallbackQuery):
    await handle_text_update(client, query, 'START', "Send the new **Start Message** text. Type `cancel` to abort.")

@Client.on_callback_query(filters.regex("^fsub_txt$"))
async def force_txt(client: Client, query: CallbackQuery):
    await handle_text_update(client, query, 'FSUB', "Send the new **Force Subscribe** text. Type `cancel` to abort.")

@Client.on_callback_query(filters.regex("^about_txt$"))
async def about_txt(client: Client, query: CallbackQuery):
    await handle_text_update(client, query, 'ABOUT', "Send the new **About Message** text. Type `cancel` to abort.")

@Client.on_callback_query(filters.regex("^reply_txt$"))
async def reply_txt(client: Client, query: CallbackQuery):
    await handle_text_update(client, query, 'REPLY', "Send the new default **Reply Message** text for unauthorized users. Type `cancel` to abort.")

@Client.on_callback_query(filters.regex("^help_txt$"))
async def help_txt(client: Client, query: CallbackQuery):
    await handle_text_update(client, query, 'HELP', "Send the new **Help Message** text. Type `cancel` to abort.")

@Client.on_callback_query(filters.regex("^support_url$"))
async def support_url_cb(client: Client, query: CallbackQuery):
    await handle_text_update(client, query, 'SUPPORT_GRP', "Send the new **Support Group URL**. Type `cancel` to abort.")

@Client.on_callback_query(filters.regex("^owner_url$"))
async def owner_url_cb(client: Client, query: CallbackQuery):
    await handle_text_update(client, query, 'OWNER_URL', "Send the new **Owner URL**. Type `cancel` to abort.")

@Client.on_callback_query(filters.regex("^network_url$"))
async def network_url_cb(client: Client, query: CallbackQuery):
    await handle_text_update(client, query, 'NETWORK_URL', "Send the new **Network URL**. Type `cancel` to abort.")
