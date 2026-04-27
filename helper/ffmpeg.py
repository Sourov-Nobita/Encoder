import os
import asyncio
import time
import re
from math import floor
from helper.utils import progress_for_pyrogram
from helper.helper_func import ftext

async def fix_video(client, message, file_path, task_dir, user_id, new_file_name, width, height, duration, watermark_url, watermark_status, metadata_status, metadata):
    """
    Video processing logic including watermark and metadata using FFmpeg.
    """
    output_path = os.path.join(task_dir, f"fixed_{new_file_name}")
    wm_path = os.path.join(task_dir, "watermark.png")

    # Base command
    cmd = ["ffmpeg", "-i", file_path]

    if watermark_url and watermark_status:
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(watermark_url) as resp:
                    if resp.status == 200:
                        with open(wm_path, "wb") as f:
                            f.write(await resp.read())
                        cmd.extend(["-i", wm_path])
                        filter_complex = f"[0:v][1:v]overlay=main_w-overlay_w-10:main_h-overlay_h-10[outv]"
                        cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", "0:a?"])
                    else:
                        watermark_status = False
        except Exception as e:
            print(f"Error downloading watermark: {e}")
            watermark_status = False

    # Metadata injection
    if metadata_status:
        metadata_val = metadata or "𝖣𝗂𝗌𝗍𝗋𝗂𝖻𝗎𝗍𝖾𝖽 𝖻𝗒 𝖶𝖾𝗂 𝖫𝖺𝗂"
        cmd.extend([
            "-metadata", f"title={metadata_val}",
            "-metadata", f"author={metadata_val}",
            "-metadata", f"artist={metadata_val}",
            "-metadata:s:v", f"title={metadata_val}",
            "-metadata:s:a", f"title={metadata_val}",
            "-metadata:s:s", f"title={metadata_val}"
        ])

    if not (watermark_url and watermark_status):
        cmd.extend(["-c", "copy"])
    else:
        cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-c:a", "copy"])

    cmd.extend([output_path, "-y"])

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        os.replace(output_path, file_path)
        return True, None
    else:
        return False, stderr.decode()

async def add_soft_subtitle(client, message, video_path, sub_path, output_path):
    """
    Muxes subtitle stream into video file.
    """
    # If the video already has subtitles, we might want to map all or be specific.
    # MKV supports most sub types.
    cmd = [
        "ffmpeg", "-i", video_path, "-i", sub_path,
        "-map", "0:v", "-map", "0:a", "-map", "1:s", "-c", "copy",
        "-c:s", "srt", # Ensure compatibility if needed
        "-disposition:s:0", "default", output_path, "-y"
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        return False, stderr.decode()
    return True, None

async def extract_all_subtitles(video_path, output_dir):
    """
    Extracts all subtitle streams from a video file.
    """
    from helper.anime_utils import mediainfo
    info = await mediainfo(video_path)
    if not info:
        return False, "Failed to get media info"

    streams = info.get('streams', [])
    subtitle_streams = [s for s in streams if s.get('codec_type') == 'subtitle']

    if not subtitle_streams:
        return False, "No subtitle streams found"

    extracted_files = []
    for i, s in enumerate(subtitle_streams):
        codec = s.get('codec_name', 'srt')
        ext = 'srt'
        if codec == 'ass': ext = 'ass'
        elif codec == 'vtt': ext = 'vtt'
        elif codec == 'mov_text': ext = 'srt'

        stream_index = s.get('index')
        output_file = os.path.join(output_dir, f"subtitle_{i+1}.{ext}")

        cmd = ["ffmpeg", "-i", video_path, "-map", f"0:{stream_index}", output_file, "-y"]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        if process.returncode == 0:
            extracted_files.append(output_file)

    if not extracted_files:
        return False, "Failed to extract any subtitles"
    return True, extracted_files

async def extract_all_audios(video_path, output_dir):
    """
    Extracts all audio streams from a video file.
    """
    from helper.anime_utils import mediainfo
    info = await mediainfo(video_path)
    if not info:
        return False, "Failed to get media info"

    streams = info.get('streams', [])
    audio_streams = [s for s in streams if s.get('codec_type') == 'audio']

    if not audio_streams:
        return False, "No audio streams found"

    extracted_files = []
    for i, s in enumerate(audio_streams):
        codec = s.get('codec_name', 'mp3')
        ext = 'mp3'
        if codec == 'aac': ext = 'm4a'
        elif codec == 'flac': ext = 'flac'
        elif codec == 'opus': ext = 'opus'
        elif codec == 'vorbis': ext = 'ogg'
        elif codec == 'ac3': ext = 'ac3'
        elif codec == 'eac3': ext = 'eac3'

        stream_index = s.get('index')
        output_file = os.path.join(output_dir, f"audio_{i+1}.{ext}")

        cmd = ["ffmpeg", "-i", video_path, "-map", f"0:{stream_index}", "-c", "copy", output_file, "-y"]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        if process.returncode != 0:
            # Try without -c copy if it fails
            cmd = ["ffmpeg", "-i", video_path, "-map", f"0:{stream_index}", output_file, "-y"]
            process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await process.communicate()

        if process.returncode == 0:
            extracted_files.append(output_file)

    if not extracted_files:
        return False, "Failed to extract any audio"
    return True, extracted_files

async def remove_all_subtitles(video_path, output_path):
    """
    Removes all subtitle streams from a video file.
    """
    cmd = ["ffmpeg", "-i", video_path, "-map", "0", "-map", "-0:s", "-c", "copy", output_path, "-y"]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        return False, stderr.decode()
    return True, None

async def remove_all_audios(video_path, output_path):
    """
    Removes all audio streams from a video file.
    """
    cmd = ["ffmpeg", "-i", video_path, "-map", "0", "-map", "-0:a", "-c", "copy", output_path, "-y"]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        return False, stderr.decode()
    return True, None

async def add_hard_subtitle(client, message, video_path, sub_path, output_path):
    """
    Burns subtitles into the video with progress bar.
    """
    from helper.anime_utils import mediainfo, editMessage, sans_fonts, convertBytes, convertTime

    duration = await mediainfo(video_path, get_duration=True)
    if not duration: duration = 1.0

    task_id = int(time.time())
    prog_file = f"prog_sub_{task_id}.txt"

    # Check for custom fonts
    fonts_dir = "fonts"
    font_args = ""
    if os.path.exists(fonts_dir) and os.listdir(fonts_dir):
        # Use the first font found as default if any exists
        font_name = os.listdir(fonts_dir)[0]
        # For the subtitles filter, we can specify the fontsdir
        font_args = f":fontsdir={fonts_dir}:force_style='FontName={font_name.split('.')[0]}'"

    # We need to escape the sub_path for the subtitles filter
    # For Windows paths (if any) or paths with colons/quotes
    escaped_sub_path = sub_path.replace("\\", "/").replace("'", "'\\''").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"subtitles='{escaped_sub_path}'{font_args}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "copy", "-progress", prog_file, output_path, "-y"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    start_time = time.time()
    filename = os.path.basename(video_path)

    async def progress_monitor():
        while True:
            is_done = process.returncode is not None
            if os.path.exists(prog_file):
                try:
                    with open(prog_file, 'r') as f:
                        text = f.read()

                    time_done = floor(int(t[-1]) / 1000000) if (t := re.findall(r"out_time_us=(\d+)", text)) else 1
                    ensize = int(s[-1]) if (s := re.findall(r"total_size=(\d+)", text)) else 0

                    diff = time.time() - start_time
                    speed = ensize / diff if diff > 0 else 0
                    percent = min(round((time_done / duration) * 100, 2), 100.0)
                    tsize = ensize / (max(percent, 0.01) / 100)
                    eta = max(round((tsize - ensize) / max(speed, 0.01)), 0)

                    tsize_str = convertBytes(tsize) if percent > 5 else "Calculating..."
                    eta_str = convertTime(eta) if percent > 5 else "Calculating..."
                    bar = floor(percent / 5) * "█" + (20 - floor(percent / 5)) * "▒"

                    progress_str = f"""‣ <b>{sans_fonts('File Name')} :</b>
<blockquote><b><i>{filename}</i></b></blockquote>

<blockquote>‣ <b>{sans_fonts('Status')} :</b> <i>{sans_fonts('Hard-subbing')}</i>
<code>[{bar}]</code> {percent}% </blockquote>

<blockquote>‣ <b>{sans_fonts('Size')} :</b> {convertBytes(ensize)} {sans_fonts('out of')} ~ {tsize_str}
‣ <b>{sans_fonts('Speed')} :</b> {convertBytes(speed)}/s
‣ <b>{sans_fonts('Time Took')} :</b> {convertTime(diff)}
‣ <b>{sans_fonts('Time Left')} :</b> {eta_str} </blockquote>"""

                    await editMessage(message, progress_str)
                except Exception:
                    pass

            if is_done:
                break
            await asyncio.sleep(8)

    monitor_task = asyncio.create_task(progress_monitor())
    stdout, stderr = await process.communicate()
    await monitor_task

    if os.path.exists(prog_file):
        os.remove(prog_file)

    if process.returncode != 0:
        return False, stderr.decode()
    return True, None
