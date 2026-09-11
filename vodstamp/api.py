import json
import time
import socket
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from .core import video_id, match_row

class ApiError(Exception):
    pass

class Http:
    def __init__(self, opener=urlopen, sleep=time.sleep):
        self.opener, self.sleep = opener, sleep

    def get(self, url, headers=None):
        for attempt in range(4):
            try:
                with self.opener(Request(url, headers=headers or {}), timeout=25) as response:
                    return json.load(response)
            except HTTPError as error:
                if (error.code == 429 or error.code >= 500) and attempt < 3:
                    try:
                        delay = max(1, float(error.headers.get('Retry-After', 2 ** (attempt + 1))))
                    except (ValueError, TypeError):
                        delay = 5
                    if delay <= 120:
                        self.sleep(delay)
                        continue
                messages = {401: 'Credenziali non valide.', 403: 'Accesso negato: verifica key, scadenza, API abilitata e quota.', 404: 'Account o risorsa non trovata.', 429: 'Limite API raggiunto. Riprova più tardi.'}
                raise ApiError(messages.get(error.code, f'Servizio non disponibile (HTTP {error.code}).')) from None
            except (URLError, socket.timeout, TimeoutError, OSError):
                raise ApiError('Connessione fallita. Verifica rete e riprova.') from None
            except (ValueError, UnicodeError):
                raise ApiError('Risposta API non valida.') from None

def youtube_range(http, url, key):
    if not key:
        raise ApiError('Serve YouTube API key. In alternativa scegli Manuale.')
    data = http.get('https://www.googleapis.com/youtube/v3/videos?' + urlencode({'part': 'liveStreamingDetails', 'id': video_id(url), 'key': key}))
    try:
        details = data['items'][0]['liveStreamingDetails']
        start, end = [datetime.fromisoformat(details[k].replace('Z', '+00:00')) for k in ('actualStartTime', 'actualEndTime')]
        if start.tzinfo is None or end.tzinfo is None or end <= start:
            raise ValueError()
        return start, end
    except (KeyError, IndexError, TypeError, ValueError):
        raise ApiError('Inizio/fine live non disponibili. VOD privato, non-live o live in corso: usa Manuale.') from None

class Riot:
    def __init__(self, http, key):
        if not key:
            raise ApiError('Inserisci Riot Personal API Key.')
        self.http, self.key = http, key

    def get(self, path, **params):
        return self.http.get('https://europe.api.riotgames.com' + path + ('?' + urlencode(params) if params else ''), {'X-Riot-Token': self.key})

    def collect(self, accounts, start, end, offset=0, progress=lambda _: None):
        owners, ids = {}, set()
        for account in accounts:
            progress('Account: ' + account)
            name, tag = account.rsplit('#', 1)
            puuid = self.get('/riot/account/v1/accounts/by-riot-id/' + quote(name, safe='') + '/' + quote(tag, safe=''))['puuid']
            owners[puuid] = account
            page = 0
            while True:
                batch = self.get('/lol/match/v5/matches/by-puuid/' + quote(puuid, safe='') + '/ids', startTime=int(start.timestamp()), endTime=int(end.timestamp()), start=page, count=100)
                ids.update(batch)
                if len(batch) < 100:
                    break
                page += 100
        rows = []
        for index, mid in enumerate(sorted(ids)):
            progress(f'Partita {index + 1}/{len(ids)}')
            row = match_row(self.get('/lol/match/v5/matches/' + quote(mid, safe='')), owners, start, end, offset)
            if row:
                rows.append(row)
        return sorted(rows, key=lambda r: (r.seconds, r.match_id))
