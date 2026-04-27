from helper.utils import auth_filter
from helper.helper_func import ftext
from pyrogram import Client, filters
from pyrogram.types import Message, BotCommand
from pyrogram.enums import ParseMode

MAIN_BOT_COMMANDS = [
    BotCommand("start", "Start the bot"),
    BotCommand("help", "Get help"),
    BotCommand("queue", "Check task queue"),
    BotCommand("clear", "Clear all queue tasks (Admin)"),
    BotCommand("stats", "System & Server info (Admin)"),
    BotCommand("batch", "Create batch link (Admin)"),
    BotCommand("genlink", "Generate single link (Admin)"),
    BotCommand("encode", "Encode a video/document"),
    BotCommand("broadcast", "Broadcast message (Admin)"),
    BotCommand("dbroadcast", "Deletable Broadcast (Admin)"),
    BotCommand("pbroadcast", "Pin Broadcast (Admin)"),
    BotCommand("users", "Check total users (Admin)"),
    BotCommand("setup", "Auto setup commands (Admin)"),
    BotCommand("settings", "Bot settings (Admin)"),
    BotCommand("usersettings", "User settings"),
    BotCommand("rename", "Manual rename a file"),
    BotCommand("autorename", "Set auto rename format"),
    BotCommand("show_format", "Show current auto rename format"),
    BotCommand("gofile", "Upload file to GoFile"),
    BotCommand("img", "Upload media to Catbox/Envs"),
    BotCommand("sub", "Add subtitles to video"),
    BotCommand("extract_sub", "Extract all subtitles"),
    BotCommand("extract_audio", "Extract all audios"),
    BotCommand("remove_sub", "Remove all subtitles"),
    BotCommand("remove_audio", "Remove all audios"),
    BotCommand("usage", "Check bot usage (Admin)"),
    BotCommand("add_font", "Add font for hardsub (Admin)"),
    BotCommand("list_font", "List fonts for hardsub (Admin)"),
    BotCommand("restart", "Restart the bot (Admin)"),
    BotCommand("reset", "Reset bot settings (Admin)"),
    BotCommand("ban", "Ban user (Admin)"),
    BotCommand("unban", "Unban user (Admin)"),
    BotCommand("flood", "Check antiflood settings (Admin)"),
    BotCommand("setflood", "Set consecutive antiflood (Admin)"),
    BotCommand("setfloodtimer", "Set timed antiflood (Admin)"),
    BotCommand("floodmode", "Set antiflood action (Admin)"),
    BotCommand("clearflood", "Enable/disable clear flood (Admin)"),
]


@Client.on_message(filters.command('setup') & auth_filter)
async def setup_command(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(ftext(client.reply_text))

    status_msg = await message.reply(ftext("⚙️ <b>Starting Auto-Setup...</b>"), parse_mode=ParseMode.HTML)

    try:
        # Set commands for current bot
        await client.set_bot_commands(MAIN_BOT_COMMANDS)
        result_text = ftext(f"✅ <b>Commands set for @{client.username}</b>\n")

        await status_msg.edit(result_text, parse_mode=ParseMode.HTML)

    except Exception as e:
        await status_msg.edit(ftext(f"❌ <b>Setup failed:</b> <code>{e}</code>"), parse_mode=ParseMode.HTML)
