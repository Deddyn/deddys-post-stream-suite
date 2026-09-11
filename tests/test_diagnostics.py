import unittest
from vodstamp.diagnostics import diagnose
from vodstamp.api import ApiError


class DiagnosticTests(unittest.TestCase):
    def test_riot_response_classification(self):
        import io
        from urllib.error import HTTPError
        from vodstamp.api import Http
        cases = [
            ({'Content-Type': 'text/html'}, b'<html>secret</html>', 'HTML access-denied page'),
            ({'cf-mitigated': 'challenge'}, b'secret', 'Cloudflare requires'),
            ({}, b'{"status":{"message":"secret","status_code":403}}', 'JSON authorization denial'),
        ]
        for headers, body, expected in cases:
            def opener(request, timeout):
                self.assertEqual(request.get_header('Accept'), 'application/json')
                self.assertIn('LoLVodTimestamps', request.get_header('User-agent'))
                raise HTTPError(request.full_url, 403, '', headers, io.BytesIO(body))
            report = diagnose('Riot', 'secret', 'Deddy#616', http=Http(opener))
            self.assertIn(expected, report)
            self.assertNotIn('secret', report)

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
                raise ApiError('Riot (HTTP 403): access denied')
        report = diagnose('Riot', 'secret', 'Deddy#616', http=Fake())
        self.assertIn('key accepted', report)
        self.assertIn('ERROR — Riot Match-v5', report)

    def test_empty_history_is_not_bad_key(self):
        class Fake:
            def get(self, url, headers=None):
                return {'puuid': 'p'} if 'by-riot-id' in url else []
        report = diagnose('Riot', 'secret', 'Deddy#616', http=Fake())
        self.assertNotIn('ERROR', report)
        self.assertIn('detail test skipped', report)

    def test_youtube_and_missing_key(self):
        class Fake:
            def get(self, url):
                return {'items':[{'liveStreamingDetails':{'actualStartTime':'2026-09-11T12:00:00Z','actualEndTime':'2026-09-11T13:00:00Z'}}]}
        self.assertIn('OK — YouTube', diagnose('YouTube', 'secret', url='https://youtu.be/abcdefghijk', http=Fake()))
        self.assertIn('Enter your key', diagnose('Riot', ''))

    def test_secret_redacted_from_errors(self):
        class Fake:
            def get(self, *args, **kwargs): raise ApiError('secret')
        self.assertNotIn('secret', diagnose('Riot', 'secret', 'Deddy#616', http=Fake()))
