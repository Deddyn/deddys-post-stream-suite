from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re
from urllib.parse import urlparse, parse_qs

ACCOUNTS = ['Deddy#616', 'Toni Bonji#PALLE', 'Bubbals#EUW']
ROLES = {'TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'}

def video_id(url):
    p = urlparse(url.strip())
    host = (p.hostname or '').lower()
    parts = p.path.strip('/').split('/')
    value = ''
    if p.scheme == 'https' and host == 'youtu.be':
        value = parts[0]
    elif p.scheme == 'https' and host in {'youtube.com', 'www.youtube.com', 'm.youtube.com'}:
        value = parse_qs(p.query).get('v', [''])[0] if p.path == '/watch' else (parts[1] if len(parts) == 2 and parts[0] in {'live', 'embed', 'shorts'} else '')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', value):
        raise ValueError('Inserisci un URL YouTube HTTPS valido.')
    return value

def manual_range(start, zone, hours):
    try:
        dt = datetime.fromisoformat(start)
        duration = float(hours)
        if not 0 < duration <= 744:
            raise ValueError()
    except ValueError:
        raise ValueError('Data: AAAA-MM-GG HH:MM:SS. Durata: da 0 a 744 ore, escluso 0.') from None
    if dt.tzinfo is None:
        try:
            tz = ZoneInfo(zone)
        except ZoneInfoNotFoundError:
            raise ValueError('Timezone non disponibile. Usa una data con offset, es. +02:00, oppure installa tzdata.') from None
        candidates = {dt.replace(tzinfo=tz, fold=f).astimezone(timezone.utc) for f in (0, 1)
                      if dt.replace(tzinfo=tz, fold=f).astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) == dt}
        if len(candidates) != 1:
            raise ValueError('Ora inesistente o ambigua per cambio ora legale. Specifica offset +01:00 o +02:00.')
        dt = candidates.pop()
    dt = dt.astimezone(timezone.utc)
    return dt, dt + timedelta(hours=duration)

def stamp(seconds):
    seconds = max(0, int(seconds))
    return f'{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}'

@dataclass
class Row:
    match_id: str
    account: str
    seconds: int
    title: str
    note: str = ''
    selected: bool = True
    raw_seconds: int = 0
    duration: int = 0

def match_row(match, owners, start, end, offset=0):
    info = match['info']
    when = datetime.fromtimestamp(info['gameStartTimestamp'] / 1000, timezone.utc)
    if not start <= when < end:
        return None
    players = info['participants']
    owned = [p for p in players if p.get('puuid') in owners]
    if not owned:
        return None
    me = min(owned, key=lambda p: list(owners).index(p['puuid']))
    champion = me['championName']
    mode = info.get('gameMode', 'Sconosciuta')
    note = 'Più account presenti: verifica prospettiva.' if len(owned) > 1 else ''
    role = me.get('teamPosition')
    if info.get('mapId') == 11 and mode == 'CLASSIC':
        rivals = [p for p in players if p.get('teamId') != me.get('teamId') and p.get('teamPosition') == role]
        if role in ROLES and len(rivals) == 1:
            title = f"{champion} vs {rivals[0]['championName']}"
            note = (note + ' Ruolo stimato da Riot; verifica eventuali lane swap.').strip()
        else:
            title = f'{champion} vs ?'
            note = (note + ' Avversario non determinabile: modifica titolo.').strip()
    else:
        title = f'{champion} - {mode}'
    seconds = int((when - start).total_seconds()) + offset
    if seconds < 0:
        note = (note + ' Offset negativo: timestamp limitato a zero.').strip()
    duration = int(info.get('gameDuration', 0))
    if info.get('gameEndTimestamp', 0) > info['gameStartTimestamp']:
        duration = int((info['gameEndTimestamp'] - info['gameStartTimestamp']) / 1000)
    return Row(match['metadata']['matchId'], owners[me['puuid']], max(0, seconds), title, note,
               raw_seconds=int((when - start).total_seconds()), duration=duration)

def output(rows):
    return '\n'.join(f'{stamp(r.seconds)} - {r.title}' for r in rows if r.selected)
