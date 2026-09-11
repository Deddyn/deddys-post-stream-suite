"""Small diagnostic requests. Reports contain no credentials or raw responses."""
from urllib.parse import quote
from .api import Http, Riot, ApiError, youtube_range


def diagnose(provider, key, accounts='', url='', http=None):
    report = []
    stage = 'Configuration'
    try:
        if not key.strip() and provider != 'YouTube':
            raise ValueError('Enter your key in Riot API.txt.')
        if any(c.isspace() for c in key.strip()):
            raise ValueError('The key contains internal whitespace. Copy it again from the portal.')
        http = http or Http()
        if provider == 'YouTube':
            stage = 'YouTube: ' + ('API access' if key.strip() else 'public page without a key') + ' and VOD metadata'
            start, end = youtube_range(http, url, key.strip())
            report.append(f'OK — {stage}.\nStart: {start.isoformat()}\nEnd: {end.isoformat()}')
        else:
            names = [a.strip() for a in accounts.split(';') if a.strip()]
            if not names or any('#' not in a or not all(a.rsplit('#', 1)) for a in names):
                raise ValueError('Enter at least one Name#TAG account; separate accounts with ;')
            riot = Riot(http, key.strip())
            for index, account in enumerate(names, 1):
                # Index rather than user text prevents accidentally pasted secrets entering reports.
                stage = f'Riot Account-v1 EUROPE — account {index}'
                name, tag = account.rsplit('#', 1)
                data = riot.get('/riot/account/v1/accounts/by-riot-id/' + quote(name, safe='') + '/' + quote(tag, safe=''))
                puuid = data['puuid']
                report.append(f'OK — {stage}: account found, key accepted.')
                stage = f'Riot Match-v5 EUROPE — match history for account {index}'
                ids = riot.get('/lol/match/v5/matches/by-puuid/' + quote(puuid, safe='') + '/ids', start=0, count=1)
                report.append(f'OK — {stage}: access granted.')
                if ids:
                    stage = f'Riot Match-v5 EUROPE — match details for account {index}'
                    detail = riot.get('/lol/match/v5/matches/' + quote(ids[0], safe=''))
                    if 'info' not in detail:
                        raise ValueError('Incomplete match details.')
                    report.append(f'OK — {stage}: readable.')
                else:
                    report.append('INFO — No recent matches: detail test skipped. This does not mean the key is invalid.')
            report.append('The Riot test does not use the VOD date: it checks credentials and API access separately.')
    except (ApiError, ValueError) as error:
        report.append(f'ERROR — {stage}\n{error}')
    except Exception:
        report.append(f'ERROR — {stage}\nUnexpected response. Retry; no sensitive data is included in this report.')
    result = '\n\n'.join(report)
    return result.replace(key.strip(), '[key hidden]') if key.strip() else result
