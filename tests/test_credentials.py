import tempfile
import unittest
from pathlib import Path
from vodstamp.credentials import load_riot_key

class CredentialTests(unittest.TestCase):
    def test_file_formats_and_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'Riot API.txt'
            with self.assertRaises(ValueError): load_riot_key(path)
            path.write_text('\ufefftest-key\n', encoding='utf-8')
            self.assertEqual(load_riot_key(path), 'test-key')
            for value in ['', 'key one\nkey two']:
                path.write_text(value)
                with self.assertRaises(ValueError) as error: load_riot_key(path)
                self.assertNotIn('key one', str(error.exception))
