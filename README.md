# Deddy’s Post Stream Suite

Turn your League of Legends streams individual match videos (and also generate Timestamps for your Youtube VODs descriptions).

Paste your YouTube livestream VOD link, enter your EUW accounts, and generate a chronological list of your games. The app matches your Riot match history with the stream’s start and end times automatically.

Want to save a great game? Download it directly from YouTube, or add the matching Twitch VOD link to download from Twitch. Review the suggested trim, adjust it if needed, and save your match as an MP4.

**Windows • EUW accounts • Your own Riot API key required • No YouTube API key needed**

**[Download for Windows](https://github.com/Deddyn/deddys-post-stream-suite/releases/latest)**

<img width="1171" height="841" alt="Screenshot 2026-09-13 011545" src="https://github.com/user-attachments/assets/0b400874-5973-4f1d-954a-113c441bd964" />


## Quick start — Windows 10/11, 64-bit

1. Open this repository’s **Releases** page and download the Windows ZIP asset, not GitHub’s automatic “Source code” ZIP.
2. Right-click the ZIP, choose **Extract All**, and keep the whole extracted folder together. Do not run the app inside the ZIP.
3. Get your own Riot API key using the steps below. Paste it into the app's **Riot Personal API Key** field, or into the marked space in the included `Riot API.txt` file.
4. Open `DeddysPostStreamSuite.exe`. Python is included. The release also contains TwitchDownloaderCLI, yt-dlp, FFmpeg/FFprobe and Deno; no separate setup is needed.
5. Replace the example EUW accounts with yours, using `Name#TAG; OtherName#TAG`. This version supports **EUW accounts**, not every Riot server.
6. Choose your city’s timezone and enter the YouTube link to a **public, completed livestream VOD**.
7. Click **Find Matches**. Start and End fill automatically. Review titles, include/exclude rows and click **Copy timestamps**.

The application is unsigned. Windows may display a publisher warning. Verify that your ZIP came from this repository’s release and compare its SHA-256 with the published checksum; do not disable antivirus protection.

## Get your own Riot API key

1. Open the [Riot Developer Portal](https://developer.riotgames.com/) and sign in with your Riot account.
2. Choose [Register Product](https://developer.riotgames.com/app-type), then the personal-project option for your own private use.
3. Give your personal application any name you like. Select **League of Legends**, complete the form and submit it. You can copy this description if it matches your intended use:

   ```text
   I use this desktop tool privately to match my EUW League of Legends games to my livestream VODs, create timestamps, and trim recordings of my own games.
   ```

4. In the portal, open **Apps**, select the application you just registered and, once approved, copy its **Personal API Key**.
5. Paste the key into the tool's **Riot Personal API Key** field and click **Test Riot**. The tool saves it locally in `Riot API.txt` in the app folder, so you do not need to paste it again next time. You can also edit the marked key space in that file directly.

For more information, see [Riot's API key guide](https://developer.riotgames.com/docs/portal).

## Fields and timestamps

- **YouTube URL:** required to determine the stream interval. No YouTube API key is needed. The app reads public livestream metadata; it never substitutes the upload date. Consent pages, private videos, ongoing streams or website changes can prevent this.
- **Twitch URL:** optional, and must refer to the same broadcast. It enables the Twitch download buttons.
- **Start / End:** automatically displayed as `DD-MM-YYYY HH:MM:SS` in your selected timezone.
- **Timezone:** city-based entries show GMT offsets, including seasonal offsets. Conversion uses the stream date and automatically handles daylight-saving time. Fractional offsets and fixed GMT options are available; choose a city for automatic seasonal adjustment.
- **YouTube offset:** seconds added to match timestamps and YouTube trims.
- **Twitch offset:** separate seconds added to the match’s position relative to YouTube’s stream start. If Twitch started 30 seconds earlier, use `+30`; if 30 seconds later, use `-30`. It does not inherit the YouTube offset.

Only your Riot API key is saved between launches. Links and dates start empty; offsets, timezone and example accounts return to their defaults. The key stays in the local, unencrypted `Riot API.txt` file; keep it private. Updates: extract the new release into a new folder and replace its blank `Riot API.txt` with your existing file.

## Review and download matches

All queues are included. Games starting within `[stream start, stream end)` are deduplicated across accounts and sorted chronologically. A match already running when the stream began is excluded. The timestamp marks game start, not champion select. Riot may not provide very old match histories.

Summoner’s Rift CLASSIC matchups use Riot’s estimated role. Lane swaps can be wrong; unknown opponents appear as `Champion vs ?`. Other modes use `Champion - Mode`. Double-click a title to edit it. Space or the include/exclude buttons control copied timestamps. If several configured accounts occur in one match, the first listed account present takes priority.

Each row has **Youtube** and **Twitch** buttons. Click one to review the proposed trim: 10 seconds before game start and 20 seconds after its Riot-reported end. Edit the start/end seconds if needed, then choose a new MP4 filename. Existing files are not overwritten. Downloading does not require that row to be included in the timestamp list.

One download runs at a time. Progress appears in the main window; keep it open until completion. Accurate YouTube cuts can require re-encoding. The app does not automatically access browser cookies or private/subscriber-only VODs. A failed download may leave partial files. Cropped VODs or multiple cuts may require more than a constant offset; check your first clip manually.

## Troubleshooting

- **Missing key:** paste your key into the app's **Riot Personal API Key** field, or into the marked space in the included `Riot API.txt`. A missing file is recreated automatically.
- **Key could not be saved:** extract the app into a folder you can write to, then paste the key again.
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

## (For Italians) Piselloni come state?

Spero che questa Repo possa essere utile a qualcuno, io l'ho creata principalmente per me e poter pubblicare più facilmente sui socials i games che ho giocato on stream. Se a qualcuno interessasse, questi sono i miei socials e contatti:
- Twitch: https://www.twitch.tv/deddy__/
- YouTube: https://www.youtube.com/@DeddynYT
- TikTok: https://www.tiktok.com/@deddy__twtv
- Instagram: https://www.instagram.com/deddy_ttv/
- Discord: https://discord.gg/UCjksf3yJh
