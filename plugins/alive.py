from helper.utils import auth_filter
import asyncio
from platform import python_version as pyver
from pyrogram import Client, filters, __version__ as pyrogram_version
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import OWNER_ID, Var
from helper.helper_func import ftext, flbl

SUPPORT_CHAT = "Vecna_Bots"
START_PIC = Var.CUSTOM_BANNER

@Client.on_message(filters.command(["alive", "Alive"]))
async def alive_handler(client: Client, message: Message):
    try:
        await message.delete()
    except Exception:
        pass

    accha = await message.reply("⚡")
    await asyncio.sleep(0.4)
    await accha.edit_text(ftext("DING DONG ꨄ︎ ALIVE.."))
    await asyncio.sleep(0.4)
    await accha.edit_text(ftext("DING DONG ꨄ︎ ALIVE......"))
    await asyncio.sleep(0.4)
    await accha.edit_text(ftext("I AM ONLINE!"))
    await asyncio.sleep(0.4)
    await accha.delete()

    buttons = [
        [
            InlineKeyboardButton(flbl("Owner"), url=f"tg://user?id={OWNER_ID}"),
            InlineKeyboardButton(flbl("Support"), url=f"https://t.me/{SUPPORT_CHAT}"),
        ],
        [
            InlineKeyboardButton(
                flbl("Add me to your group"),
                url=f"https://t.me/{client.username}?startgroup=true",
            ),
        ],
    ]

    caption = (
        f"<b>{ftext('Hey, I am')} 『<a href='https://t.me/{client.username}'>{client.name}</a>』</b>\n"
        f"   ━━━━━━━━━━━━━━━━━━━\n"
        f"  » <b>{ftext('My Owner')}:</b> <a href='tg://user?id={OWNER_ID}'>Owner</a>\n"
        f"  \n"
        f"  » <b>{ftext('Pyrogram Version')}:</b> <code>{pyrogram_version}</code>\n"
        f"  \n"
        f"  » <b>{ftext('Python Version')}:</b> <code>{pyver()}</code>\n"
        f"   ━━━━━━━━━━━━━━━━━━━"
    )

    await message.reply_photo(
        START_PIC,
        caption=ftext(caption),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
