# Deddy’s Post Stream Suite

Turn your League of Legends streams into ready-to-copy timestamps and individual match videos.

Paste your YouTube livestream VOD link, enter your EUW accounts, and generate a chronological list of your games. The app matches your Riot match history with the stream’s start and end times automatically.

Want to save a great game? Download it directly from YouTube, or add the matching Twitch VOD link to download from Twitch. Review the suggested trim, adjust it if needed, and save your match as an MP4.

**Windows • EUW accounts • Your own Riot API key required • No YouTube API key needed**

**[Download for Windows](https://github.com/Deddyn/deddys-post-stream-suite/releases/latest)**

<img width="937" height="835" alt="Deddy’s Post Stream Suite interface showing VOD inputs, match timestamps and download buttons" src="https://github.com/user-attachments/assets/7e3d2fd5-fd07-4555-b54b-365c7e0470a5" />

## Quick start — Windows 10/11, 64-bit

1. Open this repository’s **Releases** page and download the Windows ZIP asset, not GitHub’s automatic “Source code” ZIP.
2. Right-click the ZIP, choose **Extract All**, and keep the whole extracted folder together. Do not run the app inside the ZIP.
3. Create `Riot API.txt` next to `DeddysPostStreamSuite.exe`, or rename `Riot API.example.txt`. Paste only your own key into that file, save as UTF-8, and close the editor. Make sure Windows has not named it `Riot API.txt.txt`.
4. Open `DeddysPostStreamSuite.exe`. Python is included. The release also contains TwitchDownloaderCLI, yt-dlp, FFmpeg/FFprobe and Deno; no separate setup is needed.
5. Replace the example EUW accounts with yours, using `Name#TAG; OtherName#TAG`. This version supports **EUW accounts**, not every Riot server.
6. Choose your city’s timezone and enter the YouTube link to a **public, completed livestream VOD**.
7. Click **Generate timestamps**. Start and End fill automatically. Review titles, include/exclude rows and click **Copy**.

The application is unsigned. Windows may display a publisher warning. Verify that your ZIP came from this repository’s release and compare its SHA-256 with the published checksum; do not disable antivirus protection.

## Get your own Riot API key

1. Open the [Riot Developer Portal](https://developer.riotgames.com/) and sign in with your Riot account.
2. Choose [Register Product](https://developer.riotgames.com/app-type), then the personal-project option for your own private use.
3. Select League of Legends/Standard APIs where requested. Provide a truthful description of your use, the repository URL and any other requested details.
4. Submit the application. Check its messages/status in the portal and answer any questions from Riot. Approval is not guaranteed.
5. Once approved, open your registered project and copy its **Personal API Key** into the local `Riot API.txt` file.
6. Click **Test Riot** in the app. It checks account lookup, match history and one recent match for each configured account.

Example description to adapt truthfully: “I use this desktop tool privately to match my EUW League of Legends games to my livestream VODs, create timestamps, and trim recordings of my own games.”

The portal’s temporary **Development Key expires every 24 hours**. Personal keys are intended for personal/private use, while public-facing products require appropriate Riot approval and production access. A public source repository does not itself grant permission to operate a public API service. Never distribute your key or assume that individual keys remove Riot’s policy requirements. See [Riot’s key and registration guidance](https://developer.riotgames.com/docs/portal).

The underlined **Riot Personal API Key** label opens the application page. The tool reads the file at launch and before generating/testing, so you can replace an expired key without changing code. Keys are masked in the UI, excluded from Git and release packaging, and never included in diagnostic reports. The local text file is unencrypted: do not share it or include it in screenshots/ZIPs.

## Fields and timestamps

- **YouTube URL:** required to determine the stream interval. No YouTube API key is needed. The app reads public livestream metadata; it never substitutes the upload date. Consent pages, private videos, ongoing streams or website changes can prevent this.
- **Twitch URL:** optional, and must refer to the same broadcast. It enables the Twitch download buttons.
- **Start / End:** automatically displayed as `DD-MM-YYYY HH:MM:SS` in your selected timezone.
- **Timezone:** city-based entries show GMT offsets, including seasonal offsets. Conversion uses the stream date and automatically handles daylight-saving time. Fractional offsets and fixed GMT options are available; choose a city for automatic seasonal adjustment.
- **YouTube offset:** seconds added to match timestamps and YouTube trims.
- **Twitch offset:** separate seconds added to the match’s position relative to YouTube’s stream start. If Twitch started 30 seconds earlier, use `+30`; if 30 seconds later, use `-30`. It does not inherit the YouTube offset.

No settings or match results persist between launches. Links and dates start empty; offsets, timezone and example accounts return to their defaults. Your key file stays in place. Updates: extract the new release into a new folder and copy your private `Riot API.txt` into it.

## Review and download matches

All queues are included. Games starting within `[stream start, stream end)` are deduplicated across accounts and sorted chronologically. A match already running when the stream began is excluded. The timestamp marks game start, not champion select. Riot may not provide very old match histories.

Summoner’s Rift CLASSIC matchups use Riot’s estimated role. Lane swaps can be wrong; unknown opponents appear as `Champion vs ?`. Other modes use `Champion - Mode`. Double-click a title to edit it. Space or the include/exclude buttons control copied timestamps. If several configured accounts occur in one match, the first listed account present takes priority.

Each row has **Youtube** and **Twitch** buttons. Click one to review the proposed trim: 10 seconds before game start and 20 seconds after its Riot-reported end. Edit the start/end seconds if needed, then choose a new MP4 filename. Existing files are not overwritten. Downloading does not require that row to be included in the timestamp list.

One download runs at a time. Progress appears in the main window; keep it open until completion. Accurate YouTube cuts can require re-encoding. The app does not automatically access browser cookies or private/subscriber-only VODs. A failed download may leave partial files. Cropped VODs or multiple cuts may require more than a constant offset; check your first clip manually.

## Troubleshooting

- **Missing key:** create the UTF-8 file next to the executable, not inside `_internal`.
- **Riot 403:** run Test Riot and compare the same current key in the official portal. A 403 alone does not prove a typo; the app distinguishes recognizable API denials from web protection responses.
- **Riot 404:** check Riot ID spelling, tag and EUW region.
- **Rate limit:** let the app wait or retry later. It respects bounded Retry-After delays.
- **YouTube metadata unavailable:** confirm the URL belongs to a completed public live, not a regular upload.
- **Downloader missing:** extract the entire release, including `tools`. Moving only the main executable is insufficient.
- **Download failed:** check the visible error and whether the VOD is still public/available. Website changes can require an updated release.
- **Wrong times:** choose the correct city and verify each platform’s offset separately.

## Development and releases

Python 3.11+ with Tkinter is required for source use. Run `python -m pip install -r requirements.txt`, restore the tools listed in `THIRD_PARTY_NOTICES.md`, and start with `python -m vodstamp`. Run tests from the repository root: `python -m unittest discover -s tests -v`.

For source setup, run `powershell -File restore_tools.ps1` to fetch the pinned tools and verify hashes. For a release build, install `pyinstaller==6.22.2`, then run `python build_release.py --version 1.0.0`. The build uses an explicit allowlist and never copies the developer’s working folder wholesale. `Riot API.txt`, downloaded videos, tools and build output are excluded from Git. Only the release ZIP contains the standalone tools.

## Credits and licenses

Created for Deddy’s streaming workflow. Thanks to [TwitchDownloader](https://github.com/lay295/TwitchDownloader), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [FFmpeg](https://ffmpeg.org/), [Gyan’s Windows builds](https://www.gyan.dev/ffmpeg/builds/), [Deno](https://deno.com/), Python, Tcl/Tk, IANA/tzdata and PyInstaller. See [third-party notices](THIRD_PARTY_NOTICES.md) and the license files shipped with the release. Third-party components retain their own licenses.

This project is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and League of Legends are trademarks or registered trademarks of Riot Games, Inc. This project is not affiliated with Twitch or YouTube.
