"""Small diagnostic requests. Reports contain no credentials or raw responses."""
from urllib.parse import quote
from .api import Http, Riot, ApiError, youtube_range


def diagnose(provider, key, accounts='', url='', http=None):
    report = []
    stage = 'Configurazione'
    try:
        if not key.strip():
            raise ValueError('Inserisci la chiave nel campo dedicato.')
        if any(c.isspace() for c in key.strip()):
            raise ValueError('La chiave contiene spazi o ritorni a capo interni. Ricopiala dal portale.')
        http = http or Http()
        if provider == 'YouTube':
            stage = 'YouTube: accesso API e metadati del VOD'
            start, end = youtube_range(http, url, key.strip())
            report.append(f'OK — YouTube: accesso e metadati live.\nInizio: {start.isoformat()}\nFine: {end.isoformat()}')
        else:
            names = [a.strip() for a in accounts.split(';') if a.strip()]
            if not names or any('#' not in a or not all(a.rsplit('#', 1)) for a in names):
                raise ValueError('Inserisci almeno un account Nome#TAG, separando gli account con ;')
            riot = Riot(http, key.strip())
            for index, account in enumerate(names, 1):
                # Index rather than user text prevents accidentally pasted secrets entering reports.
                stage = f'Riot Account-v1 EUROPE — account {index}'
                name, tag = account.rsplit('#', 1)
                data = riot.get('/riot/account/v1/accounts/by-riot-id/' + quote(name, safe='') + '/' + quote(tag, safe=''))
                puuid = data['puuid']
                report.append(f'OK — {stage}: account trovato, chiave accettata.')
                stage = f'Riot Match-v5 EUROPE — cronologia account {index}'
                ids = riot.get('/lol/match/v5/matches/by-puuid/' + quote(puuid, safe='') + '/ids', start=0, count=1)
                report.append(f'OK — {stage}: accesso consentito.')
                if ids:
                    stage = f'Riot Match-v5 EUROPE — dettaglio partita account {index}'
                    detail = riot.get('/lol/match/v5/matches/' + quote(ids[0], safe=''))
                    if 'info' not in detail:
                        raise ValueError('Dettaglio partita incompleto.')
                    report.append(f'OK — {stage}: leggibile.')
                else:
                    report.append('INFO — Nessuna partita recente: test dettaglio non eseguito. Non indica una chiave errata.')
            report.append('Il test Riot non usa la data del VOD: verifica credenziali e accesso ai servizi separatamente.')
    except (ApiError, ValueError) as error:
        report.append(f'ERRORE — {stage}\n{error}')
    except Exception:
        report.append(f'ERRORE — {stage}\nRisposta inattesa. Riprova; nessun dato sensibile incluso nel rapporto.')
    result = '\n\n'.join(report)
    return result.replace(key.strip(), '[chiave nascosta]') if key.strip() else result
