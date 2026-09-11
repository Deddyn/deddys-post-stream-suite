import json
import unittest
from vodstamp.youtube_public import parse_live_page

class PublicTests(unittest.TestCase):
    def page(self, details):
        return '<script>var ytInitialPlayerResponse = ' + json.dumps({'microformat':{'playerMicroformatRenderer':{'liveBroadcastDetails':details}}}) + ';</script>'

    def test_actual_bounds(self):
        start, end = parse_live_page(self.page({'startTimestamp':'2026-09-10T20:00:02Z','endTimestamp':'2026-09-11T00:00:02Z','isLiveNow':False}))
        self.assertEqual((end-start).total_seconds(), 14400)
        self.assertEqual(start.hour, 20)

    def test_missing_scheduled_and_invalid(self):
        for details in [{}, {'startTimestamp':'2026-09-10T20:00:02Z'}, {'startTimestamp':'2026-09-10T20:00:02Z','endTimestamp':'2026-09-11T00:00:02Z','isLiveNow':True}, {'startTimestamp':'2026-09-11','endTimestamp':'2026-09-10'}]:
            with self.assertRaises(ValueError): parse_live_page(self.page(details))
        with self.assertRaises(ValueError): parse_live_page('<html>Consent required</html>')
