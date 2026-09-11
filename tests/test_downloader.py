import unittest
from unittest.mock import patch
from pathlib import Path
from vodstamp.core import Row, match_row
from vodstamp.downloader import twitch_id, trim, command
from test_app import match, START
from datetime import timedelta

class DownloadTests(unittest.TestCase):
    def test_url(self):
        self.assertEqual(twitch_id('https://www.twitch.tv/videos/12345?t=2h'), '12345')
        for url in ['https://twitch.tv.evil/videos/12345', 'https://twitch.tv/videos/no', 'file:///videos/123', 'https://twitch.tv/name']:
            with self.assertRaises(ValueError): twitch_id(url)

    def test_timing_independent_of_youtube_offset(self):
        data = match(seconds=100)
        data['info']['gameDuration'] = 1800
        row = match_row(data, {'p':'a'}, START, START+timedelta(hours=12), 500)
        self.assertEqual(row.seconds, 600)
        self.assertEqual(trim(row, -30), (60, 1890))
        self.assertEqual(trim(row, -100), (0, 1820))
        with self.assertRaises(ValueError): trim(row, -5000)
        data['info']['gameEndTimestamp'] = data['info']['gameStartTimestamp'] + 1900000
        row = match_row(data, {'p':'a'}, START, START+timedelta(hours=12))
        self.assertEqual(row.duration, 1900)

    def test_no_duration(self):
        with self.assertRaises(ValueError): trim(Row('1', 'a', 1, 'Jax'), 0)

    def test_command_safe_paths_and_no_overwrite(self):
        with patch.object(Path, 'is_file', return_value=True):
            args = command('https://twitch.tv/videos/123', 10, 20, 'C:/A B/test.mp4')
        self.assertEqual(args[args.index('--output')+1], 'C:/A B/test.mp4')
        self.assertEqual(args[args.index('--collision')+1], 'Exit')
        self.assertEqual(args[args.index('--beginning')+1], '10s')
        self.assertEqual(args[args.index('--ending')+1], '20s')

    def test_gui_buttons(self):
        import tkinter as tk
        from vodstamp.gui import App
        root = tk.Tk()
        root.withdraw()
        try:
            with patch('vodstamp.gui.load_riot_key', return_value='fake'):
                app = App(root)
            app.rows = [Row('1', 'a', 10, 'Jax', raw_seconds=10, duration=100)]
            app.refresh()
            app.place_download_buttons()
            self.assertIn('disabled', app.download_buttons['0'].state())
            app.values['twitch'].set('https://twitch.tv/videos/123')
            app.place_download_buttons()
            self.assertNotIn('disabled', app.download_buttons['0'].state())
            app.downloading = True
            app.place_download_buttons()
            self.assertIn('disabled', app.download_buttons['0'].state())
        finally:
            for timer in root.tk.call('after', 'info'): root.after_cancel(timer)
            root.destroy()
