import asyncio
from pyrogram.types import Message, CallbackQuery
from pyrogram import filters

class ListenerTimeout(Exception):
    """Exception raised when a listener times out."""
    pass

async def listen(client, chat_id, user_id=None, filters=None, timeout=None, listener_type='message'):
    """
    Wait for an update in a specific chat (and optionally from a specific user).
    """
    key = (chat_id, user_id, listener_type)
    future = asyncio.get_event_loop().create_future()

    listener = {
        'future': future,
        'filters': filters
    }

    if key not in client._listeners:
        client._listeners[key] = []

    client._listeners[key].append(listener)

    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        if key in client._listeners and listener in client._listeners[key]:
            client._listeners[key].remove(listener)
            if not client._listeners[key]:
                del client._listeners[key]
        raise ListenerTimeout
    except Exception as e:
        if key in client._listeners and listener in client._listeners[key]:
            client._listeners[key].remove(listener)
            if not client._listeners[key]:
                del client._listeners[key]
        raise e

async def ask(client, chat_id, text, user_id=None, filters=None, timeout=None, **kwargs):
    """
    Send a message and wait for a response.
    """
    await client.send_message(chat_id, text, **kwargs)
    return await listen(client, chat_id=chat_id, user_id=user_id, filters=filters, timeout=timeout)

async def handle_listeners(client, update, listener_type='message'):
    """
    Global handler to check for pending listeners.
    """
    if isinstance(update, Message):
        chat_id = update.chat.id
        user_id = update.from_user.id if update.from_user else None
    elif isinstance(update, CallbackQuery):
        chat_id = update.message.chat.id if update.message else None
        user_id = update.from_user.id
    else:
        return False

    # Check for (chat_id, user_id, type) then (chat_id, None, type)
    for key in [(chat_id, user_id, listener_type), (chat_id, None, listener_type)]:
        if key in client._listeners and client._listeners[key]:
            # Get the oldest listener
            for listener in list(client._listeners[key]):
                if listener['filters']:
                    if not await listener['filters'](client, update):
                        continue

                if not listener['future'].done():
                    listener['future'].set_result(update)

                client._listeners[key].remove(listener)
                if not client._listeners[key]:
                    del client._listeners[key]
                return True # Update consumed by a listener
    return False
