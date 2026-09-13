import tempfile
import unittest
from pathlib import Path
from vodstamp.credentials import KEY_TEMPLATE, ensure_riot_key_file, load_riot_key, save_riot_key

class CredentialTests(unittest.TestCase):
    def test_missing_file_is_created_from_template(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'Riot API.txt'
            with self.assertRaises(ValueError):
                load_riot_key(path)
            self.assertEqual(path.read_text(encoding='utf-8'), KEY_TEMPLATE)
            self.assertIn('Paste your API Key here:', KEY_TEMPLATE)
            self.assertIn('--- Instructions ---', KEY_TEMPLATE)
            self.assertIn('https://developer.riotgames.com/', KEY_TEMPLATE)
            self.assertIn('https://developer.riotgames.com/app-type', KEY_TEMPLATE)
            self.assertIn('https://developer.riotgames.com/docs/portal', KEY_TEMPLATE)
            self.assertIn('Once approved', KEY_TEMPLATE)

    def test_ensure_never_overwrites_an_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'Riot API.txt'
            path.write_text('existing', encoding='utf-8')
            ensure_riot_key_file(path)
            self.assertEqual(path.read_text(encoding='utf-8'), 'existing')

    def test_legacy_and_template_formats(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'Riot API.txt'
            path.write_text('\ufefftest-key\n', encoding='utf-8')
            self.assertEqual(load_riot_key(path), 'test-key')
            path.write_text(KEY_TEMPLATE.replace('Paste your API Key here:', 'Paste your API Key here: same-line-key'), encoding='utf-8')
            self.assertEqual(load_riot_key(path), 'same-line-key')
            path.write_text(KEY_TEMPLATE.replace('Paste your API Key here:\n', 'Paste your API Key here:\nnext-line-key\n'), encoding='utf-8')
            self.assertEqual(load_riot_key(path), 'next-line-key')

    def test_invalid_content_does_not_leak_it_in_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'Riot API.txt'
            for value in ['', 'key one\nkey two']:
                path.write_text(value)
                with self.assertRaises(ValueError) as error: load_riot_key(path)
                self.assertNotIn('key one', str(error.exception))

    def test_save_uses_template_and_preserves_existing_instructions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'Riot API.txt'
            save_riot_key('first-key', path)
            self.assertEqual(load_riot_key(path), 'first-key')
            self.assertIn('--- Instructions ---', path.read_text(encoding='utf-8'))
            path.write_text('Paste your API Key here:\nold-key\n\n--- Instructions ---\nCustom help\n', encoding='utf-8')
            save_riot_key('replacement-key', path)
            text = path.read_text(encoding='utf-8')
            self.assertEqual(load_riot_key(path), 'replacement-key')
            self.assertIn('Custom help', text)
            self.assertNotIn('old-key', text)

    def test_save_rejects_whitespace_without_leaking_value(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'Riot API.txt'
            for value in ('', 'secret key', 'secret\nkey'):
                with self.assertRaises(ValueError) as error:
                    save_riot_key(value, path)
                if value:
                    self.assertNotIn(value, str(error.exception))
            self.assertFalse(path.exists())
