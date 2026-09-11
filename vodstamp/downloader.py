from pathlib import Path
from urllib.parse import urlparse
import re
import subprocess
import sys
from .core import video_id
from .paths import ROOT, TOOLS

CLI = ROOT / 'tools' / 'TwitchDownloaderCLI' / 'TwitchDownloaderCLI.exe'
FFMPEG = TOOLS / 'ffmpeg' / 'ffmpeg.exe'

def twitch_id(url):
    parsed = urlparse(url.strip())
    match = re.fullmatch(r'/videos/(\d+)/?', parsed.path)
    if parsed.scheme != 'https' or parsed.hostname not in ('twitch.tv', 'www.twitch.tv', 'm.twitch.tv') or not match:
        raise ValueError('Enter a valid link such as https://www.twitch.tv/videos/123456.')
    return match[1]

def trim(row, offset, before=10, after=20):
    if row.duration <= 0:
        raise ValueError('Match duration unavailable: cannot propose a trim.')
    start = row.raw_seconds + int(offset)
    end = start + row.duration + int(after)
    start = max(0, start - int(before))
    if end <= start:
        raise ValueError('Trim ends before the VOD starts. Check the platform offset.')
    return start, end

def command(url, start, end, destination):
    if not CLI.is_file() or not FFMPEG.is_file():
        raise ValueError('TwitchDownloaderCLI or FFmpeg missing. Extract the complete release ZIP, including tools.')
    if start < 0 or end <= start:
        raise ValueError('Invalid time range.')
    return [str(CLI), 'videodownload', '--id', twitch_id(url), '--beginning', f'{start}s', '--ending', f'{end}s',
            '--output', str(destination), '--ffmpeg-path', str(FFMPEG), '--trim-mode', 'Exact', '--collision', 'Exit']

def youtube_command(url, start, end, destination):
    source = TOOLS / 'yt-dlp' / 'yt-dlp.exe'
    if not source.is_file() or not FFMPEG.is_file():
        raise ValueError('yt-dlp or FFmpeg missing. Extract the complete release ZIP, including tools.')
    if start < 0 or end <= start:
        raise ValueError('Invalid time range.')
    canonical = 'https://www.youtube.com/watch?v=' + video_id(url)
    args = [str(source), '--ignore-config', '--no-playlist', '--no-overwrites', '--newline',
            '--ffmpeg-location', str(FFMPEG), '--download-sections', f'*{start}-{end}',
            '--force-keyframes-at-cuts', '--merge-output-format', 'mp4', '--remux-video', 'mp4',
            '--output', str(destination).replace('%', '%%')]
    deno = TOOLS / 'deno' / 'deno.exe'
    if deno.is_file():
        args += ['--js-runtimes', 'deno:' + str(deno)]
    return args + [canonical]

def download(args, report, destination=None):
    # No shell; URL and paths cannot become executable commands.
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), encoding='utf-8', errors='replace') as process:
        tail = []
        for line in process.stdout:
            line = line.strip()
            if line:
                tail = (tail + [line])[-5:]
                report(line[-300:])
        if process.wait() != 0:
            raise ValueError('Download failed. ' + '\n'.join(tail))
    output = Path(destination or args[args.index('--output') + 1])
    if not output.is_file() or output.stat().st_size == 0:
        raise ValueError('The downloader did not produce a valid video file.')
