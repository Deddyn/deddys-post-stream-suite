import unittest
from datetime import datetime, timezone
from vodstamp.timezones import OPTIONS, DEFAULT, resolve

class TimezoneTests(unittest.TestCase):
    def test_rome_dst(self):
        zone = resolve(DEFAULT)
        self.assertEqual(datetime(2026, 1, 1, tzinfo=timezone.utc).astimezone(zone).hour, 1)
        self.assertEqual(datetime(2026, 7, 1, tzinfo=timezone.utc).astimezone(zone).hour, 2)

    def test_fractional_and_extreme_offsets(self):
        self.assertTrue(any('GMT+05:45' in x and 'Kathmandu' in x for x in OPTIONS))
        self.assertTrue(any('GMT-12:00' in x for x in OPTIONS))
        self.assertTrue(any('GMT+14:00' in x for x in OPTIONS))
        for name in OPTIONS:
            self.assertIsNotNone(resolve(name))
