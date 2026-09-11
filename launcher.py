import sys
from vodstamp.gui import main

if __name__ == '__main__':
    if '--self-test' in sys.argv:
        import json
        import subprocess
        import tkinter as tk
        from datetime import datetime, timezone
        from vodstamp.paths import ROOT, TOOLS
        from vodstamp.timezones import resolve, DEFAULT
        from vodstamp.gui import App
        root = tk.Tk()
        root.withdraw()
        app = App(root)
        root.update_idletasks()
        result = {'gui': True, 'winter_hour': datetime(2026, 1, 1, tzinfo=timezone.utc).astimezone(resolve(DEFAULT)).hour,
                  'summer_hour': datetime(2026, 7, 1, tzinfo=timezone.utc).astimezone(resolve(DEFAULT)).hour}
        for tool, args in [('TwitchDownloaderCLI/TwitchDownloaderCLI.exe', ['--version']), ('yt-dlp/yt-dlp.exe', ['--version']),
                           ('ffmpeg/ffmpeg.exe', ['-version']), ('ffmpeg/ffprobe.exe', ['-version']), ('deno/deno.exe', ['--version'])]:
            process = subprocess.run([str(TOOLS / tool)] + args, capture_output=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
            result[tool] = (process.returncode == 0 or
                            (tool.startswith('TwitchDownloaderCLI/') and process.returncode == 1
                             and b'TwitchDownloaderCLI 1.56.5' in process.stdout + process.stderr))
        (ROOT / 'self-test.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        root.destroy()
        sys.exit(0 if all(result.values()) else 1)
    else:
        main()
