from pathlib import Path
from urllib.parse import urlparse
import re
import subprocess
import sys
from .core import video_id

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / 'tools' / 'TwitchDownloaderCLI' / 'TwitchDownloaderCLI.exe'
FFMPEG = Path.home() / 'Downloads' / 'TwitchDownloaderGUI-1.56.5-Windows-x64' / 'ffmpeg.exe'

def twitch_id(url):
    parsed = urlparse(url.strip())
    match = re.fullmatch(r'/videos/(\d+)/?', parsed.path)
    if parsed.scheme != 'https' or parsed.hostname not in ('twitch.tv', 'www.twitch.tv', 'm.twitch.tv') or not match:
        raise ValueError('Inserisci un link https://www.twitch.tv/videos/123456 valido.')
    return match[1]

def trim(row, offset, before=10, after=20):
    if row.duration <= 0:
        raise ValueError('Durata partita non disponibile: impossibile proporre il ritaglio.')
    start = row.raw_seconds + int(offset)
    end = start + row.duration + int(after)
    start = max(0, start - int(before))
    if end <= start:
        raise ValueError('Il ritaglio termina prima dell’inizio del VOD. Controlla l’offset della piattaforma.')
    return start, end

def command(url, start, end, destination):
    if not CLI.is_file() or not FFMPEG.is_file():
        raise ValueError('TwitchDownloaderCLI o FFmpeg non trovato. Controlla la cartella tools e TwitchDownloader originale.')
    if start < 0 or end <= start:
        raise ValueError('Intervallo non valido.')
    return [str(CLI), 'videodownload', '--id', twitch_id(url), '--beginning', f'{start}s', '--ending', f'{end}s',
            '--output', str(destination), '--ffmpeg-path', str(FFMPEG), '--trim-mode', 'Exact', '--collision', 'Exit']

def youtube_command(url, start, end, destination):
    source = ROOT / 'yt-dlp'
    if not source.is_file() or not FFMPEG.is_file():
        raise ValueError('yt-dlp o FFmpeg non trovato.')
    if start < 0 or end <= start:
        raise ValueError('Intervallo non valido.')
    canonical = 'https://www.youtube.com/watch?v=' + video_id(url)
    args = [sys.executable, str(source), '--ignore-config', '--no-playlist', '--no-overwrites', '--newline',
            '--ffmpeg-location', str(FFMPEG), '--download-sections', f'*{start}-{end}',
            '--force-keyframes-at-cuts', '--merge-output-format', 'mp4', '--remux-video', 'mp4',
            '--output', str(destination).replace('%', '%%')]
    deno = Path.home() / '.deno' / 'bin' / 'deno.exe'
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
            raise ValueError('Download fallito. ' + '\n'.join(tail))
    output = Path(destination or args[args.index('--output') + 1])
    if not output.is_file() or output.stat().st_size == 0:
        raise ValueError('Il downloader non ha prodotto un file video valido.')
