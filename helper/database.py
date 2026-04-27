import motor.motor_asyncio
import uuid
import base64
import asyncio
from datetime import datetime, timedelta

class MongoDB:
    _instances = {}

    def __new__(cls, uri: str, db_name: str):
        if (uri, db_name) not in cls._instances:
            instance = super().__new__(cls)
            instance.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            instance.database_obj = instance.client[db_name]
            instance.user_data = instance.database_obj["users"]
            instance.channel_data = instance.database_obj["channels"]
            instance.bot_settings = instance.database_obj["bot_settings"]
            instance.batch_data = instance.database_obj["batch_links"]
            instance.backup_map = instance.database_obj["backup_map"]
            instance.approval_config = instance.database_obj["approval_config"]
            instance.bot_configs = instance.database_obj["bot_configs"]

            cls._instances[(uri, db_name)] = instance
        return cls._instances[(uri, db_name)]

    async def initialize(self):
        """Initializes database indexes and other async setup."""
        try:
            # Create indexes for backup_map to speed up migration and lookups
            await self.backup_map.create_index([("backup_channel_id", 1), ("backup_msg_id", 1)])
        except Exception as e:
            print(f"Failed to create indices: {e}")

    async def save_batch(self, channel_id: int, file_ids: list) -> str:
        """Saves a list of file IDs and their channel, returns a unique key."""
        key = str(uuid.uuid4().hex[:8])
        await self.batch_data.insert_one(
            {"_id": key, "channel_id": channel_id, "ids": file_ids}
        )
        return key

    async def get_batch(self, key: str) -> tuple | None:
        """Retrieves channel_id and a list of file IDs by its unique key."""
        data = await self.batch_data.find_one({"_id": key})
        return (data.get("channel_id"), data.get("ids")) if data else (None, None)

    async def add_backup_mapping(self, original_chat_id: int, original_msg_id: int, backup_msg_id: int, backup_channel_id: int):
        """Stores a mapping from an original message to its backup."""
        await self.backup_map.update_one(
            {"_id": f"{original_chat_id}:{original_msg_id}"},
            {"$set": {"backup_msg_id": backup_msg_id, "backup_channel_id": backup_channel_id}},
            upsert=True
        )

    async def get_backup_msg_id(self, original_chat_id: int, original_msg_id: int) -> tuple | None:
        """Retrieves the backup message ID and channel ID for an original message."""
        data = await self.backup_map.find_one({"_id": f"{original_chat_id}:{original_msg_id}"})
        if data:
            return data.get("backup_msg_id"), data.get("backup_channel_id")
        return None

    async def update_backup_mapping_during_migration(self, old_backup_channel_id: int, old_backup_msg_id: int, new_backup_channel_id: int, new_backup_msg_id: int):
        """Updates all backup mappings that pointed to an old message in an old backup channel to the new one."""
        await self.backup_map.update_many(
            {"backup_channel_id": old_backup_channel_id, "backup_msg_id": old_backup_msg_id},
            {"$set": {"backup_channel_id": new_backup_channel_id, "backup_msg_id": new_backup_msg_id}}
        )

    async def is_backed_up(self, original_chat_id: int, original_msg_id: int) -> bool:
        """Checks if a backup mapping exists for a message."""
        count = await self.backup_map.count_documents({"_id": f"{original_chat_id}:{original_msg_id}"})
        return count > 0

    async def save_settings(self, session_name: str, settings: dict):
        """Saves the bot's legacy settings to the database."""
        await self.bot_settings.update_one(
            {"_id": session_name},
            {"$set": {"settings": settings}},
            upsert=True
        )

    async def load_settings(self, session_name: str) -> dict | None:
        """Loads the bot's legacy settings from the database."""
        data = await self.bot_settings.find_one({"_id": session_name})
        return data.get("settings") if data else None

    async def save_bot_setting(self, key: str, value):
        """Saves a single bot-wide setting."""
        await self.bot_settings.update_one({'_id': 'global_config'}, {'$set': {key: value}}, upsert=True)
    
    async def load_bot_setting(self, key: str, default=None):
        """Loads a single bot-wide setting."""
        config = await self.bot_settings.find_one({'_id': 'global_config'})
        return config.get(key, default) if config else default

    async def save_support_ui_setting(self, key: str, value):
        """Saves a Support Bot UI setting."""
        await self.bot_settings.update_one({'_id': 'support_ui_config'}, {'$set': {key: value}}, upsert=True)

    async def load_support_ui_setting(self, key: str, default=None):
        """Loads a Support Bot UI setting."""
        config = await self.bot_settings.find_one({'_id': 'support_ui_config'})
        return config.get(key, default) if config else default
        
    async def set_auto_approval(self, channel_id: int, status: bool):
        """Enable or disable auto approval for a specific channel."""
        if status:
            await self.approval_config.update_one({'_id': channel_id}, {'$set': {'enabled': True}}, upsert=True)
        else:
            await self.approval_config.delete_one({'_id': channel_id})

    async def is_auto_approval_enabled(self, channel_id: int) -> bool:
        """Check if auto approval is enabled for a channel."""
        doc = await self.approval_config.find_one({'_id': channel_id})
        return doc is not None

    async def get_auto_approval_channels(self) -> list:
        """Get a list of all channels with auto approval enabled."""
        cursor = self.approval_config.find({'enabled': True})
        return [doc['_id'] async for doc in cursor]

    async def set_channels(self, channels: list[int]):
        await self.user_data.update_one(
            {"_id": 1},
            {"$set": {"channels": channels}},
            upsert=True
        )
    
    async def get_channels(self) -> list[int]:
        data = await self.user_data.find_one({"_id": 1})
        return data.get("channels", []) if data else []
    
    async def add_channel_user(self, channel_id: int, user_id: int):
        await self.channel_data.update_one(
            {"_id": channel_id},
            {"$addToSet": {"users": user_id}},
            upsert=True
        )

    async def remove_channel_user(self, channel_id: int, user_id: int):
        await self.channel_data.update_one(
            {"_id": channel_id},
            {"$pull": {"users": user_id}}
        )

    async def get_channel_users(self, channel_id: int) -> list[int]:
        doc = await self.channel_data.find_one({"_id": channel_id})
        return doc.get("users", []) if doc else []
        
    async def is_user_in_channel(self, channel_id: int, user_id: int) -> bool:
        doc = await self.channel_data.find_one(
            {"_id": channel_id, "users": {"$in": [user_id]}},
            {"_id": 1}
        )
        return doc is not None

    async def present_user(self, user_id: int) -> bool:
        found = await self.user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_user(self, user_id: int, ban: bool = False):
        await self.user_data.update_one(
            {'_id': user_id},
            {'$setOnInsert': {'ban': ban}},
            upsert=True
        )

    async def full_userbase(self) -> list[int]:
        user_docs = self.user_data.find()
        return [doc['_id'] async for doc in user_docs]

    async def del_user(self, user_id: int):
        await self.user_data.delete_one({'_id': user_id})

    async def ban_user(self, user_id: int):
        await self.user_data.update_one({'_id': user_id}, {'$set': {'ban': True}})

    async def unban_user(self, user_id: int):
        await self.user_data.update_one({'_id': user_id}, {'$set': {'ban': False}})

    async def is_banned(self, user_id: int) -> bool:
        user = await self.user_data.find_one({'_id': user_id})
        return user.get('ban', False) if user else False

    async def save_link_channel(self, channel_id: int):
        """Save a channel to link sharing system"""
        await self.user_data.update_one(
            {"_id": "link_channels"},
            {"$addToSet": {"channels": channel_id}},
            upsert=True
        )

    async def remove_link_channel(self, channel_id: int) -> bool:
        """Remove a channel from link sharing system"""
        result = await self.user_data.update_one(
            {"_id": "link_channels"},
            {"$pull": {"channels": channel_id}}
        )
        return result.modified_count > 0

    async def get_link_channels(self) -> list:
        """Get all link sharing channels"""
        data = await self.user_data.find_one({"_id": "link_channels"})
        return data.get("channels", []) if data else []

    async def is_link_channel(self, channel_id: int) -> bool:
        """Check if channel is in link sharing system"""
        data = await self.user_data.find_one(
            {"_id": "link_channels", "channels": {"$in": [channel_id]}}
        )
        return data is not None

    async def save_invite_link(self, channel_id: int, invite_link: str, is_request: bool):
        """Save current invite link for a channel"""
        await self.user_data.update_one(
            {"_id": f"invite_{channel_id}"},
            {
                "$set": {
                    "invite_link": invite_link,
                    "is_request": is_request,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

    async def get_current_invite_link(self, channel_id: int) -> dict:
        """Get current invite link for a channel"""
        data = await self.user_data.find_one({"_id": f"invite_{channel_id}"})
        if data:
            return {
                "invite_link": data.get("invite_link"),
                "is_request": data.get("is_request", False)
            }
        return None

    async def decode_link_param(self, param: str) -> str:
        """Decode link parameter - NOT ASYNC, just helper"""
        try:
            base64_string = param.strip("=")
            base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
            string_bytes = base64.urlsafe_b64decode(base64_bytes)
            return string_bytes.decode("ascii")
        except Exception as e:
            print(f"Decode error: {e}")
            return None


    async def set_bot_config(self, username: str, key: str, value):
        """Sets a specific configuration for the bot."""
        username = username.replace("@", "")
        await self.bot_configs.update_one(
            {"_id": username},
            {"$set": {key: value}},
            upsert=True
        )

    async def get_bot_config(self, username: str) -> dict:
        """Retrieves the full configuration for a bot."""
        username = username.replace("@", "")
        data = await self.bot_configs.find_one({"_id": username})
        return data if data else {}

    async def add_bot_uri(self, username: str, uri: str):
        """Adds a MongoDB URI to a bot's list (max 3 total)."""
        username = username.replace("@", "")
        config = await self.get_bot_config(username)
        uris = config.get("db_uris", [])
        if len(uris) >= 3: return False
        if uri in uris: return True # Already exists
        uris.append(uri)
        await self.set_bot_config(username, "db_uris", uris)
        # Also update the single 'db_uri' to the first one for backward compatibility or active use
        await self.set_bot_config(username, "db_uri", uris[0])
        return True

    async def remove_bot_uri(self, username: str, index: int):
        """Removes a MongoDB URI by index."""
        username = username.replace("@", "")
        config = await self.get_bot_config(username)
        uris = config.get("db_uris", [])
        if 0 <= index < len(uris):
            uris.pop(index)
            await self.set_bot_config(username, "db_uris", uris)
            # Update the single 'db_uri' to the new first one or null
            await self.set_bot_config(username, "db_uri", uris[0] if uris else None)
            return True
        return False

    async def get_total_files_count(self) -> int:
        """Returns the total number of files in the backup mapping."""
        return await self.backup_map.count_documents({})

    async def get_mongodb_stats(self, uri: str):
        """Fetches basic stats and connection status for a MongoDB URI."""
        try:
            client = motor.motor_asyncio.AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
            # Try to get server info to check connection
            await client.server_info()

            # Get list of databases to calculate total size
            try:
                db_names = await client.list_database_names()
            except Exception:
                db_names = []

            total_size = 0
            for name in db_names:
                try:
                    db_stats = await client[name].command("dbStats")
                    total_size += db_stats.get("storageSize", 0)
                except Exception:
                    continue

            return {
                "status": "Connected ✅",
                "size": f"{total_size / (1024*1024):.2f} MB" if total_size > 0 else "Unknown (Limited Permissions)",
                "databases": len(db_names)
            }
        except Exception as e:
            return {
                "status": f"Error ❌ ({str(e)[:30]}...)",
                "size": "N/A",
                "databases": 0
            }


    async def authorize_group(self, chat_id: int):
        await self.database_obj.groups.update_one({"_id": chat_id}, {"$set": {"authorized": True}}, upsert=True)

    async def unauthorize_group(self, chat_id: int):
        await self.database_obj.groups.update_one({"_id": chat_id}, {"$set": {"authorized": False}}, upsert=True)

    async def is_group_authorized(self, chat_id: int) -> bool:
        group = await self.database_obj.groups.find_one({"_id": chat_id})
        return group.get("authorized", False) if group else False

    async def get_flood_settings(self, chat_id: int) -> dict:
        """Retrieves antiflood settings for a group."""
        group = await self.database_obj.groups.find_one({"_id": chat_id})
        return group.get("flood_settings", {}) if group else {}

    async def set_flood_settings(self, chat_id: int, key: str, value):
        """Updates a specific antiflood setting for a group."""
        await self.database_obj.groups.update_one(
            {"_id": chat_id},
            {"$set": {f"flood_settings.{key}": value}},
            upsert=True
        )

    async def add_warn(self, user_id: int, chat_id: int) -> int:
        res = await self.database_obj.warns.find_one_and_update(
            {"user_id": user_id, "chat_id": chat_id},
            {"$inc": {"count": 1}},
            upsert=True,
            return_document=True
        )
        return res.get("count", 0)

    async def get_warns(self, user_id: int, chat_id: int) -> int:
        res = await self.database_obj.warns.find_one({"user_id": user_id, "chat_id": chat_id})
        return res.get("count", 0) if res else 0

    async def reset_warns(self, user_id: int, chat_id: int):
        await self.database_obj.warns.delete_one({"user_id": user_id, "chat_id": chat_id})

    async def approve_user(self, chat_id: int, user_id: int):
        await self.database_obj.approved_users.update_one(
            {"chat_id": chat_id},
            {"$addToSet": {"users": user_id}},
            upsert=True
        )

    async def unapprove_user(self, chat_id: int, user_id: int):
        await self.database_obj.approved_users.update_one(
            {"chat_id": chat_id},
            {"$pull": {"users": user_id}}
        )

    async def is_user_approved(self, chat_id: int, user_id: int) -> bool:
        res = await self.database_obj.approved_users.find_one({"chat_id": chat_id, "users": {"$in": [user_id]}})
        return res is not None

    async def get_approved_users(self, chat_id: int) -> list:
        res = await self.database_obj.approved_users.find_one({"chat_id": chat_id})
        return res.get("users", []) if res else []

    async def unapprove_all_users(self, chat_id: int):
        await self.database_obj.approved_users.delete_one({"chat_id": chat_id})

    async def set_afk(self, user_id: int, reason: str, time: float):
        await self.database_obj.afk.update_one(
            {"_id": user_id},
            {"$set": {"reason": reason, "time": time}},
            upsert=True
        )

    async def get_afk(self, user_id: int):
        return await self.database_obj.afk.find_one({"_id": user_id})

    async def remove_afk(self, user_id: int):
        await self.database_obj.afk.delete_one({"_id": user_id})

    async def get_daily_couple(self, chat_id: int):
        return await self.database_obj.daily_couples.find_one({"_id": chat_id})

    async def set_daily_couple(self, chat_id: int, user1_id: int, user2_id: int, date: str):
        await self.database_obj.daily_couples.update_one(
            {"_id": chat_id},
            {"$set": {"user1_id": user1_id, "user2_id": user2_id, "date": date}},
            upsert=True
        )

    # --- User Specific Settings ---
    async def set_user_setting(self, user_id: int, key: str, value):
        await self.user_data.update_one(
            {"_id": user_id},
            {"$set": {key: value}},
            upsert=True
        )

    async def get_user_setting(self, user_id: int, key: str, default=None):
        user = await self.user_data.find_one({"_id": user_id})
        return user.get(key, default) if user else default

    async def get_format_template(self, user_id: int):
        return await self.get_user_setting(user_id, "format_template")

    async def set_format_template(self, user_id: int, template: str):
        await self.set_user_setting(user_id, "format_template", template)

    async def get_media_preference(self, user_id: int):
        return await self.get_user_setting(user_id, "media_preference")

    async def set_media_preference(self, user_id: int, preference: str):
        await self.set_user_setting(user_id, "media_preference", preference)

    async def get_rename_source(self, user_id: int):
        return await self.get_user_setting(user_id, "rename_source", "filename")

    async def set_temp_name(self, user_id: int, name: str):
        await self.set_user_setting(user_id, "temp_name", name)

    async def get_temp_name(self, user_id: int):
        return await self.get_user_setting(user_id, "temp_name")

    async def get_watermark_url(self, user_id: int):
        return await self.get_user_setting(user_id, "watermark_url")

    async def get_watermark_status(self, user_id: int):
        return await self.get_user_setting(user_id, "watermark_status", False)

    async def get_metadata_status(self, user_id: int):
        return await self.get_user_setting(user_id, "metadata_status", False)

    async def get_metadata(self, user_id: int):
        return await self.get_user_setting(user_id, "metadata")

    async def get_caption(self, user_id: int):
        return await self.get_user_setting(user_id, "caption")

    async def get_thumbnail(self, user_id: int):
        return await self.get_user_setting(user_id, "thumbnail")

    async def get_upload_mode(self, user_id: int):
        return await self.get_user_setting(user_id, "upload_mode", "pm")

    async def get_upload_channel(self, user_id: int):
        return await self.get_user_setting(user_id, "upload_channel")

    async def get_gofile_token(self, user_id: int):
        return await self.get_user_setting(user_id, "gofile_token")

    async def set_gofile_token(self, user_id: int, token: str):
        await self.set_user_setting(user_id, "gofile_token", token)

    async def save_encode_settings(self, settings: dict):
        """Saves bot-wide encoding settings."""
        await self.save_bot_setting("encode_settings_v2", settings)

    async def load_encode_settings(self, default: dict) -> dict:
        """Loads bot-wide encoding settings."""
        return await self.load_bot_setting("encode_settings_v2", default)

    async def get_user_encode_settings(self, user_id: int):
        """Fetches user-specific encoding settings, falling back to global ones."""
        user_settings = await self.get_user_setting(user_id, "encode_settings", {})

        # Merge with global defaults
        global_settings = await self.load_encode_settings({
            "codec": "libx264",
            "crf": "22",
            "preset": "fast",
            "audio_codec": "aac",
            "audio_bitrate": "96k",
            "bit_depth": "10bit",
            "fps": "24"
        })

        for key, value in global_settings.items():
            if key not in user_settings:
                user_settings[key] = value

        return user_settings

    async def set_user_encode_setting(self, user_id: int, key: str, value):
        """Updates a specific encoding parameter for a user."""
        user_settings = await self.get_user_setting(user_id, "encode_settings", {})
        user_settings[key] = value
        await self.set_user_setting(user_id, "encode_settings", user_settings)


