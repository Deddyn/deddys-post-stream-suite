import json
import time
import socket
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote, urlparse
from .core import video_id, match_row

class ApiError(Exception):
    pass

class Http:
    def __init__(self, opener=urlopen, sleep=time.sleep):
        self.opener, self.sleep = opener, sleep

    def get(self, url, headers=None):
        host = urlparse(url).hostname or ''
        provider = 'Riot' if host.endswith('.api.riotgames.com') else ('YouTube' if host == 'www.googleapis.com' else 'API')
        for attempt in range(4):
            try:
                request_headers = {'Accept': 'application/json', 'User-Agent': 'LoLVodTimestamps/1.0 (Windows desktop)'}
                request_headers.update(headers or {})
                with self.opener(Request(url, headers=request_headers), timeout=25) as response:
                    return json.load(response)
            except HTTPError as error:
                if (error.code == 429 or error.code >= 500) and attempt < 3:
                    try:
                        delay = max(1, float(error.headers.get('Retry-After', 2 ** (attempt + 1))))
                    except (ValueError, TypeError):
                        delay = 5
                    if delay <= 120:
                        error.close()
                        self.sleep(delay)
                        continue
                messages = {401: 'Credenziali non valide.', 403: 'Accesso negato: verifica key, scadenza, API abilitata e quota.', 404: 'Account o risorsa non trovata.', 429: 'Limite API raggiunto. Riprova più tardi.'}
                message = messages.get(error.code, 'Servizio non disponibile.')
                if provider == 'Riot' and error.code in (401, 403):
                    try:
                        body = error.read(65536)
                    except OSError:
                        body = b''
                    try:
                        payload = json.loads(body)
                    except (ValueError, UnicodeError):
                        payload = None
                    response_headers = error.headers or {}
                    html = 'text/html' in response_headers.get('Content-Type', '').lower() or body.lstrip().lower().startswith((b'<!doctype html', b'<html'))
                    challenge = response_headers.get('cf-mitigated', '').lower() == 'challenge'
                    if challenge:
                        message = 'Protezione Cloudflare: richiesta di verifica interattiva. Questa risposta non verifica la validità della chiave. Confronta il test dal portale con la stessa chiave e segnala il blocco al supporto Riot.'
                    elif html:
                        message = 'Ricevuta una pagina HTML di accesso negato, non una risposta JSON Riot. Possibile filtro web o intermediario di rete; non prova che la chiave sia errata. Verifica eventuali VPN/proxy e confronta il test dal portale con la stessa chiave.'
                    elif isinstance(payload, dict) and isinstance(payload.get('status'), dict):
                        message = 'Riot restituisce un rifiuto JSON di autorizzazione. Il codice non distingue chiave errata, revocata o altri problemi di accesso. Confronta la stessa chiave attuale nel portale e nell’app; il precedente 200 potrebbe riguardare una chiave diversa.'
                    else:
                        message = 'Accesso negato con risposta non riconosciuta. Non è possibile attribuirlo alla chiave. Confronta la stessa chiave attuale nel portale Riot e nell’app.'
                if provider == 'YouTube':
                    # Interpret only known codes; never display response text or URLs containing keys.
                    try:
                        payload = json.loads(error.read(65536))['error']
                        reasons = [e.get('reason') for e in payload.get('errors', []) + payload.get('details', []) if isinstance(e, dict)]
                    except (ValueError, KeyError, TypeError, AttributeError, OSError):
                        reasons = []
                    hints = {
                        'accessNotConfigured': 'Abilita YouTube Data API v3 nel progetto Google Cloud della chiave e riprova dopo qualche minuto.',
                        'SERVICE_DISABLED': 'Abilita YouTube Data API v3 nel progetto Google Cloud della chiave e riprova dopo qualche minuto.',
                        'quotaExceeded': 'Quota YouTube esaurita. Attendi il ripristino oppure usa Manuale.',
                        'dailyLimitExceeded': 'Quota YouTube esaurita. Attendi il ripristino oppure usa Manuale.',
                        'keyInvalid': 'YouTube API key non valida. Ricopiala dalle credenziali Google Cloud.',
                        'API_KEY_INVALID': 'YouTube API key non valida. Ricopiala dalle credenziali Google Cloud.',
                        'API_KEY_SERVICE_BLOCKED': 'Le restrizioni della chiave devono consentire YouTube Data API v3.',
                        'API_KEY_HTTP_REFERRER_BLOCKED': 'La chiave è limitata a siti web. Per questa app desktop modifica le restrizioni applicazione della chiave.',
                        'ipRefererBlocked': 'Le restrizioni applicazione della chiave bloccano questo computer. Controllale in Google Cloud.'}
                    message = next((hints[r] for r in reasons if r in hints), message)
                error.close()
                raise ApiError(f'{provider} (HTTP {error.code}): {message}') from None
            except (URLError, socket.timeout, TimeoutError, OSError):
                raise ApiError('Connessione fallita. Verifica rete e riprova.') from None
            except (ValueError, UnicodeError):
                raise ApiError('Risposta API non valida.') from None

def youtube_range(http, url, key):
    if not key:
        from .youtube_public import public_range
        try:
            return public_range(video_id(url))
        except ValueError as error:
            raise ApiError(str(error)) from None
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
