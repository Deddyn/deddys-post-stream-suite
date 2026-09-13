import unittest
from unittest.mock import patch

from vodstamp.gui import App


class FakeVar:
    def __init__(self, value=''):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeRoot:
    def __init__(self):
        self.destroyed = False

    def after(self, _delay, callback):
        self.callback = callback
        return 'timer'

    def after_cancel(self, _timer):
        pass

    def destroy(self):
        self.destroyed = True


def bare_app(value='loaded-key'):
    app = App.__new__(App)
    app.root = FakeRoot()
    app.values = {'riot': FakeVar(value)}
    app.status = FakeVar()
    app.riot_status = FakeVar()
    app._riot_dirty = False
    app._riot_loading = False
    app._riot_clean_value = value
    app._riot_save_after = None
    return app


class CredentialGuiTests(unittest.TestCase):
    def test_unedited_action_reloads_external_file_without_saving(self):
        app = bare_app()
        with patch('vodstamp.gui.load_riot_key', return_value='external-key'), patch('vodstamp.gui.save_riot_key') as save:
            self.assertEqual(app._riot_key_for_action(), 'external-key')
        self.assertEqual(app.values['riot'].get(), 'external-key')
        save.assert_not_called()

    def test_edited_action_flushes_and_uses_ui_value(self):
        app = bare_app()
        app.values['riot'].set('edited-key')
        app._riot_edited()
        with patch('vodstamp.gui.load_riot_key') as load, patch('vodstamp.gui.save_riot_key') as save:
            self.assertEqual(app._riot_key_for_action(), 'edited-key')
        save.assert_called_once_with('edited-key')
        load.assert_not_called()
        self.assertFalse(app._riot_dirty)

    def test_failed_save_does_not_fall_back_to_old_disk_key(self):
        app = bare_app()
        app.values['riot'].set('edited-key')
        app._riot_edited()
        with patch('vodstamp.gui.save_riot_key', side_effect=OSError('safe message')), patch('vodstamp.gui.load_riot_key') as load:
            self.assertEqual(app._riot_key_for_action(), 'edited-key')
        load.assert_not_called()
        self.assertTrue(app._riot_dirty)
        self.assertIn('not saved', app.riot_status.get())

    def test_programmatic_same_value_does_not_become_dirty(self):
        app = bare_app()
        app._riot_edited()
        self.assertFalse(app._riot_dirty)
        self.assertIsNone(app._riot_save_after)

    def test_successful_close_flushes_then_destroys(self):
        app = bare_app()
        app.values['riot'].set('edited-key')
        app._riot_edited()
        with patch('vodstamp.gui.save_riot_key') as save, patch('vodstamp.gui.messagebox.askyesno') as ask:
            app.close()
        save.assert_called_once_with('edited-key')
        ask.assert_not_called()
        self.assertTrue(app.root.destroyed)

    def test_failed_close_save_defaults_to_staying_open(self):
        app = bare_app()
        app.values['riot'].set('edited-key')
        app._riot_edited()
        with patch('vodstamp.gui.save_riot_key', side_effect=OSError('safe message')), patch('vodstamp.gui.messagebox.askyesno', return_value=False):
            app.close()
        self.assertFalse(app.root.destroyed)

    def test_failed_close_can_be_explicitly_discarded(self):
        app = bare_app()
        app.values['riot'].set('edited-key')
        app._riot_edited()
        with patch('vodstamp.gui.save_riot_key', side_effect=OSError('safe message')), patch('vodstamp.gui.messagebox.askyesno', return_value=True):
            app.close()
        self.assertTrue(app.root.destroyed)


if __name__ == '__main__':
    unittest.main()
