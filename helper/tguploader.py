from time import time, sleep
from traceback import format_exc
from math import floor
from os import path as ospath
from asyncio import sleep as asleep, create_task
from aiofiles.os import remove as aioremove
from pyrogram.errors import FloodWait

from config import Var
from helper.anime_utils import editMessage, sendMessage, convertBytes, convertTime, sans_fonts
from helper.reporter import rep

class TgUploader:
    def __init__(self, message, client):
        self.cancelled = False
        self.message = message
        self.__name = ""
        self.__qual = ""
        self.__client = client
        self.__start = time()
        self.__updater = time()

    async def cancel(self):
        self.cancelled = True

    async def upload(self, path, qual, target_chat_id=None, thumb=None):
        self.__name = ospath.basename(path)
        self.__qual = qual

        if not thumb:
            thumb = getattr(self.__client, 'thumb_path', None)

        if thumb and not ospath.exists(thumb):
            thumb = None

        as_doc = getattr(self.__client, 'upload_as_doc', Var.AS_DOC)
        dest_chat_id = target_chat_id or getattr(self.__client, 'dump_channel', None) or self.message.chat.id

        try:
            while True:
                try:
                    if as_doc:
                        return await self.__client.send_document(chat_id=dest_chat_id,
                            document=path,
                            thumb=thumb,
                            caption=f"<i>{self.__name}</i>",
                            force_document=True,
                            progress=self.progress_status
                        )
                    else:
                        return await self.__client.send_video(chat_id=dest_chat_id,
                            video=path,
                            thumb=thumb,
                            caption=f"<i>{self.__name}</i>",
                            progress=self.progress_status
                        )
                except FloodWait as e:
                    await asleep(e.value * 1.5)
                    continue
        except Exception as e:
            await rep.report(format_exc(), "error", client=self.__client)
            raise e
        finally:
            if ospath.exists(path):
                await aioremove(path)

    async def progress_status(self, current, total):
        if self.cancelled:
            raise Exception("Upload Cancelled !")
        now = time()
        diff = now - self.__start
        if (now - self.__updater) >= 7 or current == total:
            self.__updater = now
            percent = round(current / total * 100, 2)
            speed = current / diff if diff > 0 else 0
            eta = round((total - current) / speed) if speed > 0 else 0
            bar = floor(percent/5)*"█" + (20 - floor(percent/5))*"▒"
            progress_str = f"""‣ <b>{sans_fonts('Anime Name')} :</b>
<blockquote><b><i>{self.__name}</i></b></blockquote>

<blockquote>‣ <b>{sans_fonts('Status')} :</b> <i>{sans_fonts('Uploading')}</i>
<code>[{bar}]</code> {percent}% </blockquote>

<blockquote>‣ <b>{sans_fonts('Size')} :</b> {convertBytes(current)} {sans_fonts('out of')} ~ {convertBytes(total)}
‣ <b>{sans_fonts('Speed')} :</b> {convertBytes(speed)}/s
‣ <b>{sans_fonts('Time Took')} :</b> {convertTime(diff)}
‣ <b>{sans_fonts('Time Left')} :</b> {convertTime(eta)} </blockquote>

<blockquote>‣ <b>{sans_fonts('File(s) Encoded')} :</b> <code>{Var.QUALS.index(self.__qual) + 1} / {len(Var.QUALS)}</code></blockquote>"""

            create_task(editMessage(self.message, progress_str))
