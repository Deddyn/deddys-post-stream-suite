import unittest
from vodstamp.diagnostics import diagnose
from vodstamp.api import ApiError


class DiagnosticTests(unittest.TestCase):
    def test_riot_stages(self):
        class Fake:
            def get(self, url, headers=None):
                if 'by-riot-id' in url: return {'puuid': 'p'}
                if '/ids?' in url: return ['EUW1_1']
                return {'info': {}}
        report = diagnose('Riot', 'secret', 'Deddy#616', http=Fake())
        self.assertEqual(report.count('OK —'), 3)
        self.assertNotIn('secret', report)

    def test_failure_pinpoints_match_access(self):
        class Fake:
            def get(self, url, headers=None):
                if 'by-riot-id' in url: return {'puuid': 'p'}
                raise ApiError('Riot (HTTP 403): accesso negato')
        report = diagnose('Riot', 'secret', 'Deddy#616', http=Fake())
        self.assertIn('chiave accettata', report)
        self.assertIn('ERRORE — Riot Match-v5', report)

    def test_empty_history_is_not_bad_key(self):
        class Fake:
            def get(self, url, headers=None):
                return {'puuid': 'p'} if 'by-riot-id' in url else []
        report = diagnose('Riot', 'secret', 'Deddy#616', http=Fake())
        self.assertNotIn('ERRORE', report)
        self.assertIn('test dettaglio non eseguito', report)

    def test_youtube_and_missing_key(self):
        class Fake:
            def get(self, url):
                return {'items':[{'liveStreamingDetails':{'actualStartTime':'2026-09-11T12:00:00Z','actualEndTime':'2026-09-11T13:00:00Z'}}]}
        self.assertIn('OK — YouTube', diagnose('YouTube', 'secret', url='https://youtu.be/abcdefghijk', http=Fake()))
        self.assertIn('Inserisci la chiave', diagnose('Riot', ''))

    def test_secret_redacted_from_errors(self):
        class Fake:
            def get(self, *args, **kwargs): raise ApiError('secret')
        self.assertNotIn('secret', diagnose('Riot', 'secret', 'Deddy#616', http=Fake()))
