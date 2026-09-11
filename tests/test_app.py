import io
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch
from vodstamp.core import *
from vodstamp.api import Http, Riot, ApiError, youtube_range
from vodstamp import settings

START = datetime(2026, 9, 11, 12, tzinfo=timezone.utc)

def match(mid='EUW1_1', seconds=60, mode='CLASSIC', role='TOP'):
    return {'metadata': {'matchId': mid}, 'info': {'gameStartTimestamp': (START.timestamp() + seconds) * 1000, 'mapId': 11, 'gameMode': mode, 'participants': [
        {'puuid': 'p', 'championName': 'Jax', 'teamId': 100, 'teamPosition': role},
        {'puuid': 'q', 'championName': 'Garen', 'teamId': 200, 'teamPosition': 'TOP'}]}}

class CoreTests(unittest.TestCase):
    def test_urls(self):
        for url in ['https://youtu.be/abcdefghijk?t=1', 'https://www.youtube.com/watch?v=abcdefghijk', 'https://youtube.com/live/abcdefghijk']:
            self.assertEqual(video_id(url), 'abcdefghijk')
        for url in ['https://youtube.com.evil/watch?v=abcdefghijk', 'file:///abcdefghijk', 'https://youtube.com/watch?v=short']:
            with self.assertRaises(ValueError): video_id(url)

    def test_timezones(self):
        a, b = manual_range('2026-09-11 14:00:00', 'Europe/Rome', '12')
        self.assertEqual(a, START)
        self.assertEqual((b-a).total_seconds(), 43200)
        for dt in ['2026-03-29 02:30:00', '2026-10-25 02:30:00']:
            with self.assertRaises(ValueError): manual_range(dt, 'Europe/Rome', '12')
        self.assertEqual(manual_range('2026-10-25 02:30:00+01:00', 'invalid', '1')[0].hour, 1)
        for hours in ['nan', '-1', '0', 'inf']:
            with self.assertRaises(ValueError): manual_range('2026-09-11', 'UTC', hours)

    def test_matchup_and_bounds(self):
        end = START + timedelta(hours=12)
        row = match_row(match(), {'p': 'Deddy#616'}, START, end)
        self.assertEqual(output([row]), '00:01:00 - Jax vs Garen')
        row.selected = False
        self.assertEqual(output([row]), '')
        for seconds in [-1, 43200]:
            self.assertIsNone(match_row(match(seconds=seconds), {'p':'a'}, START, end))
        self.assertIsNotNone(match_row(match(seconds=0), {'p':'a'}, START, end))
        self.assertEqual(match_row(match(mode='ARAM'), {'p':'a'}, START, end).title, 'Jax - ARAM')
        self.assertEqual(match_row(match(role=''), {'p':'a'}, START, end).title, 'Jax vs ?')
        self.assertIn('Più account', match_row(match(), {'p':'a','q':'b'}, START, end).note)
        self.assertEqual(stamp(90061), '25:01:01')
        self.assertEqual(match_row(match(), {'p':'a'}, START, end, -120).seconds, 0)

    def test_settings_no_secrets(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            settings.save({'zone':'UTC', 'riot':'SECRET', 'youtube':'SECRET'}, path)
            self.assertNotIn('SECRET', path.read_text())
            self.assertEqual(settings.load(path), {'zone':'UTC'})
            path.write_text('broken')
            self.assertEqual(settings.load(path), {})

class ApiTests(unittest.TestCase):
    def test_retry_and_redaction(self):
        calls, sleeps = [], []
        def opener(request, timeout):
            calls.append(request)
            if len(calls) == 1:
                raise HTTPError('https://secret', 429, 'secret', {'Retry-After':'1'}, None)
            return io.StringIO('{"ok":true}')
        self.assertEqual(Http(opener, sleeps.append).get('https://example.com'), {'ok':True})
        self.assertEqual(sleeps, [1])
        def forbidden(*args, **kwargs):
            raise HTTPError('https://SECRET', 403, 'SECRET', {}, None)
        with self.assertRaises(ApiError) as error: Http(forbidden).get('https://example.com')
        self.assertNotIn('SECRET', str(error.exception))

    def test_youtube(self):
        class Fake:
            def get(self, url):
                return {'items':[{'liveStreamingDetails':{'actualStartTime':'2026-09-11T12:00:00Z','actualEndTime':'2026-09-11T13:00:00Z'}}]}
        self.assertEqual(youtube_range(Fake(), 'https://youtu.be/abcdefghijk', 'key')[0], START)
        with self.assertRaises(ApiError): youtube_range(Fake(), 'https://youtu.be/abcdefghijk', '')
        with patch.object(Fake, 'get', return_value={'items':[]}):
            with self.assertRaises(ApiError): youtube_range(Fake(), 'https://youtu.be/abcdefghijk', 'key')

    def test_collection_pagination_dedup_sort(self):
        class FakeRiot(Riot):
            def __init__(self): self.pages = []; self.details = []
            def get(self, path, **params):
                if 'by-riot-id' in path: return {'puuid':'p'}
                if path.endswith('/ids'):
                    self.pages.append(params)
                    return ['EUW1_1'] * 100 if params['start'] == 0 else ['EUW1_2']
                mid = path.split('/')[-1]
                self.details.append(mid)
                return match(mid, 120 if mid == 'EUW1_1' else 60)
        riot = FakeRiot()
        rows = riot.collect(ACCOUNTS, START, START + timedelta(hours=12))
        self.assertEqual([r.match_id for r in rows], ['EUW1_2','EUW1_1'])
        self.assertEqual(len(riot.details), 2)
        self.assertEqual([p['start'] for p in riot.pages], [0,100,0,100,0,100])
        self.assertTrue(all('queue' not in p for p in riot.pages))

class GuiTests(unittest.TestCase):
    def test_generation_worker(self):
        import tkinter as tk
        import time
        from vodstamp.gui import App
        root = tk.Tk()
        root.withdraw()
        try:
            with patch('vodstamp.gui.settings.load', return_value={}): app = App(root)
            app.values['source'].set('Manuale')
            app.values['start'].set('2026-09-11 12:00:00+00:00')
            app.values['riot'].set('fake-key')
            expected = [Row('1', 'Deddy#616', 60, 'Jax vs Garen')]
            with patch('vodstamp.gui.settings.save'), patch('vodstamp.gui.Riot.collect', return_value=expected):
                app.run()
                deadline = time.monotonic() + 3
                while not app.rows and time.monotonic() < deadline:
                    root.update()
                    time.sleep(0.01)
            self.assertEqual(app.rows, expected)
            self.assertEqual(app.preview.get('1.0', 'end').strip(), '00:01:00 - Jax vs Garen')
        finally:
            for timer in root.tk.call('after', 'info'):
                root.after_cancel(timer)
            root.destroy()

    def test_selection_preview_copy(self):
        import tkinter as tk
        from vodstamp.gui import App
        root = tk.Tk()
        root.withdraw()
        try:
            with patch('vodstamp.gui.settings.load', return_value={}): app = App(root)
            app.rows = [Row('1','a',61,'Jax vs Garen'), Row('2','a',121,'Ahri - ARAM')]
            app.refresh()
            root.update()
            app.tree.selection_set('0')
            app.toggle()
            self.assertEqual(output(app.rows), '00:02:01 - Ahri - ARAM')
            app.copy()
            self.assertEqual(root.clipboard_get(), '00:02:01 - Ahri - ARAM')
            app.select_all(True)
            self.assertEqual(len(output(app.rows).splitlines()), 2)
        finally:
            for timer in root.tk.call('after', 'info'):
                root.after_cancel(timer)
            root.destroy()

if __name__ == '__main__':
    unittest.main()
