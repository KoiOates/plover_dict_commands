#!/usr/bin/env python

import os
import tempfile
import unittest

import plover_dict_commands as pdc

from plover.config import DictionaryConfig
from plover.oslayer.config import CONFIG_DIR
from plover_dict_commands import priority_dict, toggle_dict, \
                                 solo_dict, end_solo_dict, \
                                 solo_state, SOLO_ENABLED, PREVIOUS_DICTIONARIES, \
                                 SOLO_DICT_HAS_RUN, \
                                 backup_dictionary_stack, \
                                 load_dictionary_stack_from_backup


class FakeEngine(object):

    def __init__(self, dictionaries):
        self._config_extras = {
            'one_setting': 'foobar',
            'another_setting': 42,
        }
        self._dictionaries = list(dictionaries)

    @property
    def config(self):
        d = dict(self._config_extras)
        d['dictionaries'] = list(self._dictionaries)
        return d

    @config.setter
    def config(self, config_update):
        # Only 'dictionaries' can be changed.
        assert list(config_update.keys()) == ['dictionaries']
        self._dictionaries = list(config_update['dictionaries'])


class DictCommandsTest(unittest.TestCase):

    def setUp(self):
        self.spanish = DictionaryConfig('spanish/main.json')
        self.english = DictionaryConfig('main.json')
        self.commands = DictionaryConfig('commands.json')
        self.user = DictionaryConfig('user.json')
        self.extra = DictionaryConfig('extra.json')
        self.engine = FakeEngine([
            self.user,
            self.commands,
            self.english,
            self.spanish,
        ])
        solo_state[SOLO_ENABLED] = False
        solo_state[SOLO_DICT_HAS_RUN] = False
        self.tf = tempfile.NamedTemporaryFile(delete=False)
        pdc.BACKUP_DICTIONARY_PATH = self.tf.name

    def tearDown(self):
        try:
            os.unlink(self.tf.name)
        except OSError:
            # This file gets deleted by the module being tested right now,
            # leave this here in case that changes to delete temp file
            # if necessary.
            pass

    def test_priority_dict_shortest_path_is_default(self):
        priority_dict(self.engine, 'main.json')
        self.assertEqual(self.engine.config['dictionaries'], [
            self.english,
            self.user,
            self.commands,
            self.spanish,
        ])
        priority_dict(self.engine, 'spanish/main.json')
        self.assertEqual(self.engine.config['dictionaries'], [
            self.spanish,
            self.english,
            self.user,
            self.commands,
        ])

    def test_priority_dict_multiple(self):
        priority_dict(self.engine, 'user.json, spanish/main.json, commands.json')
        self.assertEqual(self.engine.config['dictionaries'], [
            self.user,
            self.spanish,
            self.commands,
            self.english,
        ])

    def test_priority_dict_invalid(self):
        with self.assertRaises(ValueError):
            priority_dict(self.engine, 'foobar.json')

    def test_toggle_dict_shortest_path_is_default(self):
        toggle_dict(self.engine, '+main.json, -spanish/main.json')
        self.assertEqual(self.engine.config['dictionaries'], [
            self.user,
            self.commands,
            self.english.replace(enabled=True),
            self.spanish.replace(enabled=False),
        ])

    def test_toggle_dict_multiple(self):
        toggle_dict(self.engine, '+spanish/main.json, !commands.json, -user.json')
        self.assertEqual(self.engine.config['dictionaries'], [
            self.user.replace(enabled=False),
            self.commands.replace(enabled=False),
            self.english,
            self.spanish,
        ])

    def test_toggle_dict_invalid_toggle(self):
        with self.assertRaises(ValueError):
            toggle_dict(self.engine, '=user.json')

    def test_toggle_dict_invalid_dictionary(self):
        with self.assertRaises(ValueError):
            toggle_dict(self.engine, '+foobar.json')

    def test_solo_dict(self):
        solo_dict(self.engine, '+spanish/main.json')
        self.assertEqual(self.engine.config['dictionaries'], [
            self.user.replace(enabled=False),
            self.commands.replace(enabled=False),
            self.english.replace(enabled=False),
            self.spanish,
        ])

    def test_end_solo_dict_doesnt_delete_new_dictionaries(self):
        solo_dict(self.engine, '+spanish/main.json')
        # ...then load a new dictionary while in the temporary mode
        dictionaries = self.engine.config['dictionaries']
        dictionaries.append(self.extra)
        self.engine.config = { 'dictionaries': dictionaries }
        end_solo_dict(self.engine, '')
        self.assertEqual(self.engine.config['dictionaries'], [
            self.user,
            self.commands,
            self.english,
            self.spanish,
            self.extra,
        ])
        pass

    def test_backup_dictionaries_to_json_and_reload(self):
        original_dictionaries = self.engine.config['dictionaries']
        #import pdb; pdb.set_trace()
        backup_dictionary_stack(original_dictionaries, pdc.BACKUP_DICTIONARY_PATH)
        toggle_dict(self.engine, '-main.json')
        self.assertEqual(self.engine.config['dictionaries'], [
            self.user,
            self.commands,
            self.english.replace(enabled=False), # turned off
            self.spanish,
        ])
        restored_dictionaries = load_dictionary_stack_from_backup(pdc.BACKUP_DICTIONARY_PATH)
        self.engine.config = { 'dictionaries': restored_dictionaries }
        self.assertEqual(self.engine.config['dictionaries'], [
            self.user,
            self.commands,
            self.english,  # turned back on again after restore
            self.spanish,
        ])
        backup_dictionary_stack([], pdc.BACKUP_DICTIONARY_PATH)
        #clear the file for the next test

    def test_backed_up_dictionaries_restored_after_solo_if_backup_exists(self):
        toggle_dict(self.engine, '-main.json') #turned off before backup...
        original_dictionaries = self.engine.config['dictionaries']
        backup_dictionary_stack(original_dictionaries, pdc.BACKUP_DICTIONARY_PATH)
        toggle_dict(self.engine, '+main.json') #but normal before solo_dict

        #Now that there's a backup file, do the first solo_dict since we've run...
        solo_dict(self.engine, '+spanish/main.json')
        end_solo_dict(self.engine, '')

        self.assertEqual(self.engine.config['dictionaries'], [
            self.user,
            self.commands,
            self.english.replace(enabled=False),  # turned back off again after restore
            self.spanish,
        ])

    def test_end_solo_dict_restores_previous_state(self):
        toggle_dict(self.engine, '-main.json')
        solo_dict(self.engine, '+spanish/main.json')
        end_solo_dict(self.engine, '')
        self.assertEqual(self.engine.config['dictionaries'], [
            self.user,
            self.commands,
            self.english.replace(enabled=False),
            self.spanish,
        ])

    def test_end_solo_dict_without_first_doing_solo_1(self):
        backup_dictionary_stack([
            self.spanish.replace(enabled=False),
            self.user.replace(enabled=False),
        ], pdc.BACKUP_DICTIONARY_PATH)
        end_solo_dict(self.engine, '')
        self.assertEqual(self.engine.config['dictionaries'], [
            self.user.replace(enabled=False),
            self.commands,
            self.english,
            self.spanish.replace(enabled=False),
        ])

    def test_end_solo_dict_without_first_doing_solo_2(self):
        backup_dictionary_stack([
            self.extra,
            self.english.replace(enabled=False),
        ], pdc.BACKUP_DICTIONARY_PATH)
        end_solo_dict(self.engine, '')
        self.assertEqual(self.engine.config['dictionaries'], [
            self.user,
            self.commands,
            self.english.replace(enabled=False),
            self.spanish,
        ])


if __name__ == '__main__':
    unittest.main()
