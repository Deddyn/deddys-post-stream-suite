"""Build a portable Windows release from an explicit allowlist."""
from pathlib import Path
import argparse
import hashlib
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent

def build(version, output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    name = 'DeddysPostStreamSuite'
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed',
                    '--name', name, '--collect-all', 'tzdata', '--distpath', str(output / 'app'),
                    '--workpath', str(output / 'build'), '--specpath', str(output), str(ROOT / 'launcher.py')], cwd=ROOT, check=True)
    folder = output / 'app' / name
    for filename in ('README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'Riot API.example.txt', 'start.cmd'):
        shutil.copy2(ROOT / filename, folder / filename)
    for component in ('TwitchDownloaderCLI', 'yt-dlp', 'ffmpeg', 'deno'):
        shutil.copytree(ROOT / 'tools' / component, folder / 'tools' / component, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('*.pdb'))
    shutil.copytree(ROOT / 'licenses', folder / 'licenses', dirs_exist_ok=True)
    if any(p.name.lower() == 'riot api.txt' for p in folder.rglob('*')):
        raise RuntimeError('Private key filename found in staging!')
    archive = output / f'{name}-{version}-Windows-x64.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in folder.rglob('*'):
            if path.is_file() and path.name != 'self-test.json':
                bundle.write(path, Path(name) / path.relative_to(folder))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
    print(archive)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', default='1.0.0')
    parser.add_argument('--output', default=str(ROOT / 'dist'))
    args = parser.parse_args()
    build(args.version, args.output)
