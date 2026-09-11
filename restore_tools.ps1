$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$cache = Join-Path $root 'build/tool-cache'
New-Item -ItemType Directory -Force $cache | Out-Null
function Fetch($url, $file, $hash) {
    Invoke-WebRequest $url -OutFile $file
    if ((Get-FileHash $file -Algorithm SHA256).Hash -ne $hash) { throw "Hash mismatch: $file" }
}
New-Item -ItemType Directory -Force "$root/tools/yt-dlp", "$root/tools/deno", "$root/tools/ffmpeg" | Out-Null
Fetch 'https://github.com/yt-dlp/yt-dlp/releases/download/2026.08.19/yt-dlp.exe' "$root/tools/yt-dlp/yt-dlp.exe" '66674953fe251b89f4d08c5f0e35e0728679bd67ab3d7d05c0562af101dd3e7a'
Fetch 'https://github.com/denoland/deno/releases/download/v2.9.6/deno-x86_64-pc-windows-msvc.zip' "$cache/deno.zip" '15e5300b0ba3c3695a7621d90160a746ec9e710228cee639afa9d580f6e3cd11'
Expand-Archive "$cache/deno.zip" "$root/tools/deno" -Force
Fetch 'https://github.com/lay295/TwitchDownloader/releases/download/1.56.5/TwitchDownloaderCLI-1.56.5-Windows-x64.zip' "$cache/twitch.zip" '8b1b0695f2b1b6bf0d2535fab4b84032951cded8cf4078dfdf4d58e391c813a0'
Expand-Archive "$cache/twitch.zip" "$root/tools/TwitchDownloaderCLI" -Force
Fetch 'https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-8.1.2-essentials_build.zip' "$cache/ffmpeg.zip" 'db580001caa24ac104c8cb856cd113a87b0a443f7bdf47d8c12b1d740584a2ec'
Expand-Archive "$cache/ffmpeg.zip" "$cache/ffmpeg" -Force
$ff = Get-ChildItem "$cache/ffmpeg" -Directory | Select-Object -First 1
Copy-Item -LiteralPath "$($ff.FullName)/bin/ffmpeg.exe", "$($ff.FullName)/bin/ffprobe.exe", "$($ff.FullName)/LICENSE", "$($ff.FullName)/README.txt" -Destination "$root/tools/ffmpeg" -Force
Write-Output 'Portable tools restored. See THIRD_PARTY_NOTICES.md for licenses.'
