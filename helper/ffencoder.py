from re import findall 
from math import floor
from time import time
from os import path as ospath, makedirs
from aiofiles import open as aiopen
from aiofiles.os import remove as aioremove, rename as aiorename
from shlex import split as ssplit, quote
from asyncio import sleep as asleep, gather, create_subprocess_exec, create_task
from asyncio.subprocess import PIPE

from helper.anime_globals import ffpids_cache
from helper.anime_utils import mediainfo, convertBytes, convertTime, sendMessage, editMessage, sans_fonts
from helper.reporter import rep
from config import Var, LOGS

class FFEncoder:
    def __init__(self, message, path, name, qual, count=None, metadata_status=False, metadata=None, user_id=None):
        self.__proc = None
        self.is_cancelled = False
        self.message = message
        self.__name = name
        self.__qual = qual
        self.__count = count or f"{Var.QUALS.index(qual) + 1} / {len(Var.QUALS)}"
        self.dl_path = path
        self.__total_time = None
        self.out_path = ospath.join("encode", name)
        self.__task_id = f"{int(time())}_{id(self)}"
        self.__prog_file = f"prog_{self.__task_id}.txt"
        self.__start_time = time()
        self.__metadata_status = metadata_status
        self.__metadata = metadata
        self.__user_id = user_id

    async def progress(self):
        if not self.__total_time or not isinstance(self.__total_time, (int, float)) or self.__total_time <= 0:
            self.__total_time = 1.0
        while not (self.__proc is None or self.is_cancelled):
            if self.__proc.returncode is not None:
                break
            async with aiopen(self.__prog_file, 'r+') as p:
                text = await p.read()
            if text:
                time_done = floor(int(t[-1]) / 1000000) if (t := findall(r"out_time_us=(\d+)", text)) else 1
                ensize = int(s[-1]) if (s := findall(r"total_size=(\d+)", text)) else 0
                
                diff = time() - self.__start_time
                speed = ensize / diff if diff > 0 else 0
                percent = min(round((time_done/self.__total_time)*100, 2), 100.0)
                tsize = ensize / (max(percent, 0.01)/100)
                eta = max(round((tsize-ensize)/max(speed, 0.01)), 0)

                tsize_str = convertBytes(tsize) if percent > 5 else "Calculating..."
                eta_str = convertTime(eta) if percent > 5 else "Calculating..."
    
                bar = floor(percent/5)*"█" + (20 - floor(percent/5))*"▒"
                
                progress_str = f"""‣ <b>{sans_fonts('Anime Name')} :</b>
<blockquote><b><i>{self.__name}</i></b></blockquote>

<blockquote>‣ <b>{sans_fonts('Status')} :</b> <i>{sans_fonts('Encoding')}</i>
<code>[{bar}]</code> {percent}% </blockquote>

<blockquote>‣ <b>{sans_fonts('Size')} :</b> {convertBytes(ensize)} {sans_fonts('out of')} ~ {tsize_str}
‣ <b>{sans_fonts('Speed')} :</b> {convertBytes(speed)}/s
‣ <b>{sans_fonts('Time Took')} :</b> {convertTime(diff)}
‣ <b>{sans_fonts('Time Left')} :</b> {eta_str} </blockquote>

<blockquote>‣ <b>{sans_fonts('File(s) Encoded')} :</b> <code>{self.__count}</code></blockquote>"""
            
                await editMessage(self.message, progress_str)
                if (prog := findall(r"progress=(\w+)", text)) and prog[-1] == 'end':
                    break
            await asleep(3)
    
    async def start_encode(self):
        makedirs("encode", exist_ok=True)

        # Get duration before renaming
        self.__total_time = await mediainfo(self.dl_path, get_duration=True)

        if ospath.exists(self.__prog_file):
            await aioremove(self.__prog_file)
    
        async with aiopen(self.__prog_file, 'w+'):
            LOGS.info(f"Progress Temp {self.__prog_file} Generated !")
            pass
        
        dl_npath = ospath.join("encode", f"in_{self.__task_id}.mkv")
        out_npath = ospath.join("encode", f"out_{self.__task_id}.mkv")
        await aiorename(self.dl_path, dl_npath)
        
        # Get dynamic settings from client or database
        client = self.message._client
        if self.__user_id:
            s = await client.mongodb.get_user_encode_settings(self.__user_id)
        else:
            s = client.encode_settings

        codec = quote(str(s.get("codec", "libx264")))
        crf = quote(str(s.get("crf", "22")))
        preset = quote(str(s.get("preset", "fast")))
        audio_codec = quote(str(s.get("audio_codec", "aac")))
        audio_bitrate = quote(str(s.get("audio_bitrate", "96k")))
        bit_depth = str(s.get("bit_depth", "10bit"))
        fps = quote(str(s.get("fps", "24")))

        # Scale based on quality
        scale = {
            "1080": "1920:1080",
            "720": "1280:720",
            "480": "854:480",
            "360": "640:360"
        }.get(self.__qual, None)

        v_filter = f"scale={scale}," if scale else ""
        v_filter += f"fps={fps}"

        pix_fmt = "yuv420p10le" if bit_depth == "10bit" else "yuv420p"

        # Build FFmpeg command as a list
        cmd = ["ffmpeg", "-i", dl_npath]

        if self.__qual == 'HDRip':
            cmd.extend(["-c", "copy"])
        else:
            cmd.extend([
                "-preset", preset,
                "-c:v", codec,
                "-crf", crf,
                "-vf", v_filter,
                "-pix_fmt", pix_fmt,
                "-c:a", audio_codec,
                "-b:a", audio_bitrate
            ])

        cmd.extend(["-map", "0", "-c:s", "copy", "-progress", self.__prog_file])

        if self.__metadata_status:
            metadata_val = self.__metadata or "𝖣𝗂𝗌𝗍𝗋𝗂𝖻𝗎𝗍𝖾𝖽 𝖻𝗒 𝖶𝖾𝗂 𝖫𝖺𝗂"
            cmd.extend([
                "-metadata", f"title={metadata_val}",
                "-metadata", f"author={metadata_val}",
                "-metadata", f"artist={metadata_val}",
                "-metadata:s:v", f"title={metadata_val}",
                "-metadata:s:a", f"title={metadata_val}",
                "-metadata:s:s", f"title={metadata_val}"
            ])

        cmd.extend([out_npath, "-y"])
        
        LOGS.info(f'FFmpeg command: {" ".join(quote(x) for x in cmd)}')
        self.__proc = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        proc_pid = self.__proc.pid
        ffpids_cache.append(proc_pid)
        _, return_code = await gather(create_task(self.progress()), self.__proc.wait())
        ffpids_cache.remove(proc_pid)
        
        await aiorename(dl_npath, self.dl_path)
        if ospath.exists(self.__prog_file):
            await aioremove(self.__prog_file)
        
        if self.is_cancelled:
            if ospath.exists(out_npath):
                await aioremove(out_npath)
            return
        
        if return_code == 0:
            if ospath.exists(out_npath):
                await aiorename(out_npath, self.out_path)
            return self.out_path
        else:
            if ospath.exists(out_npath):
                try: await aioremove(out_npath)
                except: pass
            err_text = (await self.__proc.stderr.read()).decode().strip()
            await rep.report(err_text, "error", client=self.message._client)
            raise Exception(f"FFmpeg failed: {err_text}")
            
    async def cancel(self):
        self.is_cancelled = True
        if self.__proc is not None:
            try:
                self.__proc.kill()
            except Exception:
                pass
