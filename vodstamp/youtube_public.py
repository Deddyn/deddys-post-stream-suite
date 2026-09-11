"""Read public live metadata only; never download video or execute page scripts."""
import json
import re
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError


def parse_live_page(page):
    decoder = json.JSONDecoder()
    for marker in re.finditer(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*', page):
        try:
            player, _ = decoder.raw_decode(page[marker.end():])
            details = player['microformat']['playerMicroformatRenderer']['liveBroadcastDetails']
            if details.get('isLiveNow'):
                continue
            start, end = [datetime.fromisoformat(details[k].replace('Z', '+00:00')) for k in ('startTimestamp', 'endTimestamp')]
            if start.tzinfo and end.tzinfo and end > start:
                return start, end
        except (ValueError, KeyError, TypeError):
            continue
    raise ValueError('Metadati pubblici di inizio/fine live non disponibili. Inserisci una YouTube API key oppure scegli Manuale. Non viene usata la data di pubblicazione.')


def public_range(video, opener=urlopen):
    request = Request('https://www.youtube.com/watch?v=' + video, headers={
        'User-Agent': 'LoLVodTimestamps/1.0 (Windows desktop)', 'Accept-Language': 'en-US,en;q=0.9'})
    try:
        with opener(request, timeout=25) as response:
            page = response.read(8 * 1024 * 1024 + 1)
        if len(page) > 8 * 1024 * 1024:
            raise ValueError('Pagina YouTube troppo grande. Usa API key o Manuale.')
        return parse_live_page(page.decode('utf-8', errors='replace'))
    except (URLError, OSError, TimeoutError):
        raise ValueError('Pagina pubblica YouTube non accessibile. Usa API key o Manuale.') from None
