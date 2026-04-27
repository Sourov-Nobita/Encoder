
import pyrogram
import static_ffmpeg
static_ffmpeg.add_paths()
from pyrogram import Client, filters, handlers
import pyrogram.enums
from pyrogram.enums import ParseMode
from helper.custom_listen import listen, ask, handle_listeners

# Global Root Fix for RecursionError
# Monkeypatch Client.on_message to automatically include filters.incoming
# This prevents the bot from reacting to its own messages by default.
_original_on_message = Client.on_message

def _patched_on_message(*args, **kwargs):
    """
    Patched version of on_message to automatically include filters.incoming.
    Handles both instance-level (@app.on_message) and class-level (@Client.on_message) decorators.
    """

    def _apply_incoming(flt):
        if flt is not None:
            filter_str = str(flt)
            if "incoming" not in filter_str and "outgoing" not in filter_str and "me" not in filter_str:
                return flt & pyrogram.filters.incoming
            return flt
        return pyrogram.filters.incoming

    # Determine if this is a bound call (app.on_message) or unbound (Client.on_message)
    if args and isinstance(args[0], Client):
        # Bound: (self, filters=None, group=0)
        new_args = list(args)
        if len(new_args) > 1:
            new_args[1] = _apply_incoming(new_args[1])
        else:
            kwargs["filters"] = _apply_incoming(kwargs.get("filters"))
        return _original_on_message(*new_args, **kwargs)
    else:
        # Unbound: (filters=None, group=0)
        # When called as @Client.on_message, 'filters' is the first positional argument.
        new_args = list(args)
        if len(new_args) > 0:
            new_args[0] = _apply_incoming(new_args[0])
        else:
            kwargs["filters"] = _apply_incoming(kwargs.get("filters"))
            # In unbound call with keyword filters, we MUST ensure filters is not in kwargs
            # if we are going to pass it positionally, or just keep it in kwargs.
            # Actually, _original_on_message is a method, so calling it unboundly
            # requires passing something as 'self'.
            # If we just pass through to _original_on_message, it handles the 'self' expectation.
            pass

        return _original_on_message(*new_args, **kwargs)

Client.on_message = _patched_on_message
import sys
import asyncio
from datetime import datetime
from config import LOGGER, PORT, OWNER_ID, Var
from helper import MongoDB

version = "v1.0.0"

class Bot(Client):
    _bot_instances = []

    def __init__(self, config, custom_db_uri=None, custom_db_name=None, plugins=None, master_mongodb=None, parent_name=None):
        self._bot_instances.append(self)
        self.master_mongodb = master_mongodb
        self.parent_name = parent_name
        if plugins is None:
            plugins = {"root": "plugins"}
        session = config["session"]
        workers = config["workers"]
        fsub = config["fsubs"]
        token = config["token"]
        admins = config["admins"]
        messages = config.get("messages", {})
        auto_del = config["auto_del"]

        # Determine DB URI and Name
        db_uri = custom_db_uri or config["db_uri"]
        db_name = custom_db_name or config["db_name"]

        api_id = int(config["api_id"])
        api_hash = config["api_hash"]
        protect = config["protect"]
        disable_btn = config["disable_btn"]

        super().__init__(
            name=session, api_hash=api_hash, api_id=api_id,
            plugins=plugins, workers=workers, bot_token=token
        )
        self.LOGGER = LOGGER
        self.name = session
        self.fsub = fsub
        self.owner = OWNER_ID
        self.fsub_dict = {}
        self.admins = list(set(admins + [OWNER_ID]))
        self.messages = messages
        self.auto_del = auto_del
        self.req_fsub = {}
        self.disable_btn = disable_btn
        self.reply_text = messages.get('REPLY', 'Do not send any useless message in the bot.')
        self.initial_db_uri = db_uri
        self.mongodb = MongoDB(db_uri, db_name)

        self.req_channels = []
        self.background_tasks = set()

        self.log_channel = Var.LOG_CHANNEL
        self.thumbnail = None
        self.thumb_path = f"{session.replace('@', '').replace('.', '_').replace(' ', '_').replace(':', '_')}_thumb.jpg"
        self.upload_as_doc = Var.AS_DOC
        self.encode_quality = "all"
        self.bot_mode = "auto_encode"
        self.encode_destination = "channel"
        self.encode_settings = {
            "codec": "libx264",
            "crf": "22",
            "preset": "fast",
            "audio_codec": "aac",
            "audio_bitrate": "96k",
            "bit_depth": "10bit",
            "fps": "24"
        }
        self.encode_tasks = {}
        self.renaming_operations = {}
        self.subtitle_sessions = {}
        self.user_tasks = {}
        self._listeners = {}

        # Register global handlers for listeners
        self.add_handler(handlers.MessageHandler(self._handle_all_messages), group=-1)
        self.add_handler(handlers.CallbackQueryHandler(self._handle_all_callback_queries), group=-1)

    async def _handle_all_messages(self, client, message):
        """Global handler to intercept messages for listeners."""
        if await handle_listeners(client, message, listener_type='message'):
            message.stop_propagation()

    async def _handle_all_callback_queries(self, client, query):
        """Global handler to intercept callback queries for listeners."""
        if await handle_listeners(client, query, listener_type='callback_query'):
            query.stop_propagation()

    async def listen(self, chat_id, user_id=None, filters=None, timeout=None, listener_type='message'):
        return await listen(self, chat_id, user_id, filters, timeout, listener_type)

    async def ask(self, chat_id, text, user_id=None, filters=None, timeout=None, **kwargs):
        return await ask(self, chat_id, text, user_id, filters, timeout, **kwargs)

    def get_current_settings(self):
        """Returns the dictionary for the legacy settings system."""
        return {
            "admins": self.admins,
            "messages": self.messages,
            "auto_del": self.auto_del,
            "disable_btn": self.disable_btn,
            "reply_text": self.reply_text,
            "fsub": self.fsub
        }

    async def start(self):
        await super().start()
        await self.mongodb.initialize()
        # Ensure master_mongodb is initialized if it's separate from mongodb
        if self.master_mongodb and self.master_mongodb is not self.mongodb:
            await self.master_mongodb.initialize()
        usr_bot_me = await self.get_me()
        self.username = usr_bot_me.username
        self.uptime = datetime.now()

        await self.mongodb.save_bot_setting('master_username', self.username)

        # Auto Command Setup
        from plugins.auto_setup import MAIN_BOT_COMMANDS
        try:
            await self.set_bot_commands(MAIN_BOT_COMMANDS)
            self.LOGGER(__name__, self.name).info(f"Auto-setup commands for @{self.username}")
        except Exception as e:
            self.LOGGER(__name__, self.name).error(f"Failed to auto-setup commands: {e}")

        # Choose the source for settings
        source_db = self.mongodb

        # Load bot-specific config
        bot_config = await self.mongodb.get_bot_config(self.username)

        self.log_channel = await source_db.load_bot_setting('log_channel', Var.LOG_CHANNEL)
        
        self.thumbnail = await source_db.load_bot_setting('thumbnail')
        self.upload_as_doc = await source_db.load_bot_setting('upload_as_doc', Var.AS_DOC)
        self.metadata_status = await source_db.load_bot_setting('metadata_status', False)
        self.encode_quality = await source_db.load_bot_setting('encode_quality', "all")
        self.bot_mode = await source_db.load_bot_setting('bot_mode', "auto_encode")
        self.encode_destination = await source_db.load_bot_setting('encode_destination', "channel")
        self.dump_channel = await source_db.load_bot_setting('dump_channel')
        self.encode_settings = await source_db.load_encode_settings(self.encode_settings)

        if self.thumbnail:
            import os
            if not os.path.exists(self.thumb_path):
                try:
                    if isinstance(self.thumbnail, str) and (self.thumbnail.startswith("http://") or self.thumbnail.startswith("https://")):
                        from helper.anime_utils import get_session
                        session = await get_session()
                        async with session.get(self.thumbnail) as resp:
                            if resp.status == 200:
                                with open(self.thumb_path, "wb") as f:
                                    f.write(await resp.read())
                                self.LOGGER(__name__, self.name).info("Restored custom thumbnail from URL.")
                    else:
                        # Download to a temporary path first to ensure it's fully downloaded before renaming
                        temp_path = await self.download_media(self.thumbnail)
                        if temp_path:
                            if os.path.exists(self.thumb_path): os.remove(self.thumb_path)
                            os.rename(temp_path, self.thumb_path)
                            self.LOGGER(__name__, self.name).info("Restored custom thumbnail from FileID.")
                except Exception as e:
                    self.LOGGER(__name__, self.name).error(f"Failed to restore thumbnail: {e}")

        
        self.LOGGER(__name__, self.name).info("All modern settings loaded and validated.")
        
        # Load session-based settings (like FSub)
        saved_settings = await source_db.load_settings(self.name)
        if saved_settings:
            self.LOGGER(__name__, self.name).info("Found legacy saved settings, merging them.")
            base_messages = self.messages.copy()
            saved_messages = saved_settings.get("messages", {})
            for key, value in saved_messages.items():
                if value: base_messages[key] = value
            self.messages = base_messages
            
            saved_admins = saved_settings.get("admins", [])
            self.admins = list(set(self.admins + saved_admins + [OWNER_ID]))
            
            if saved_fsub := saved_settings.get("fsub"): self.fsub = saved_fsub
            
            self.disable_btn = saved_settings.get("disable_btn", self.disable_btn)
            self.reply_text = saved_settings.get("reply_text", self.reply_text)
        
        self.fsub_dict = {}
        if self.fsub:
            for channel_id, needs_request, timer in self.fsub:
                try:
                    chat = await self.get_chat(channel_id)
                    invite_link = chat.invite_link
                    if not invite_link and timer <= 0:
                        invite_link = (await self.create_chat_invite_link(channel_id, creates_join_request=needs_request)).invite_link
                    self.fsub_dict[channel_id] = [chat.title, invite_link, needs_request, timer]
                    if needs_request: self.req_channels.append(channel_id)
                except Exception as e:
                    self.LOGGER(__name__, self.name).error(f"Error processing FSub channel {channel_id}: {e}.")
            # FSub requests are tracked bot-specifically in self.mongodb
            await self.mongodb.set_channels(self.req_channels)

        if not self.dump_channel:
            self.LOGGER(__name__, self.name).warning("No Dump channel is set!")
        else:
            try:
                dump_chat = await self.get_chat(self.dump_channel)
                test = await self.send_message(chat_id=dump_chat.id, text="Bot is online.")
                await test.delete()
            except Exception as e:
                self.LOGGER(__name__, self.name).warning(e)
                self.LOGGER(__name__, self.name).warning(f"Make sure bot is Admin in Dump Channel. Current Value {self.dump_channel}")

        self.LOGGER(__name__, self.name).info(f"Bot Started on @{usr_bot_me.username} !!")
        self.username = usr_bot_me.username

    def create_background_task(self, coro):
        """Creates and tracks a background task."""
        task = asyncio.create_task(coro)
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        return task

    async def stop(self, *args):
        if self in self._bot_instances:
            self._bot_instances.remove(self)
        await super().stop()
        self.LOGGER(__name__, self.name).info("Bot stopped.")
