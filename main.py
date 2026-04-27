

import asyncio
import json
import os
from bot import Bot
from pyrogram import compose
from helper import MongoDB
from aiohttp import web
from config import PORT

async def hello(request):
    return web.Response(text="Bot is running!")

async def start_server():
    app = web.Application()
    app.router.add_get("/", hello)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(PORT))
    await site.start()
    print(f"Web server started on port {PORT}")

async def main():
    # Start web server for Heroku/Render port binding
    asyncio.create_task(start_server())

    app = []

    setups = []
    if os.path.exists("setup.json"):
        try:
            with open("setup.json", "r") as f:
                setups = json.load(f)
        except json.JSONDecodeError:
            print("ERROR: Could not parse setup.json. Please ensure it is a valid JSON file.")

    if not setups:
        # Fallback to environment variables if setup.json is missing or empty
        env_config = {
            "session": os.environ.get("SESSION_NAME", "FileStoreBot"),
            "token": os.environ.get("BOT_TOKEN"),
            "api_id": os.environ.get("API_ID"),
            "api_hash": os.environ.get("API_HASH"),
            "workers": int(os.environ.get("WORKERS", "8")),
            "db_uri": os.environ.get("MONGODB_URI"),
            "db_name": os.environ.get("DATABASE_NAME", "Cluster0"),
            "fsubs": [], # Can be configured via bot commands
            "auto_del": int(os.environ.get("AUTO_DEL", "0")),
            "messages": {},
            "admins": [int(x) for x in os.environ.get("ADMINS", "").split() if x],
            "protect": os.environ.get("PROTECT_CONTENT", "False").lower() == "true",
            "disable_btn": False
        }
        if env_config["token"] and env_config["api_id"] and env_config["api_hash"] and env_config["db_uri"]:
            setups.append(env_config)
        else:
            if not os.path.exists("setup.json"):
                print("FATAL ERROR: setup.json not found and required environment variables are missing.")
                return

    for config in setups:
        # Check for custom bot config (like MongoDB URI) for the master bot
        master_session = config["session"]
        # Since we use username as ID for configuration, we'll try to find master config by its session name first
        # as it might not have a username yet before starting.
        master_custom_config = {}
        # We need a temp mongodb instance to check for master bot's custom config
        temp_mongodb = MongoDB(config["db_uri"], config["db_name"])
        await temp_mongodb.initialize()
        master_custom_config = await temp_mongodb.get_bot_config(master_session)

        master_uri = master_custom_config.get("db_uri")
        master_db_name = master_custom_config.get("db_name")

        master_bot = Bot(config, custom_db_uri=master_uri, custom_db_name=master_db_name)
        app.append(master_bot)


    if not app:
        print("No valid bot configurations found in setup.json. Exiting.")
        return

    await compose(app)


async def runner():
    await main()

if __name__ == "__main__":
    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        print("Bot stopped manually.")
    except Exception as e:
        print(f"An unexpected error occurred during startup: {e}")
