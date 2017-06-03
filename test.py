#!/usr/bin/env python

import unittest

from plover.config import DictionaryConfig

from plover_dict_commands import priority_dict, toggle_dict


class FakeEngine(object):

    def __init__(self, dictionaries):
        self._config = {
            'one_setting': 'foobar',
            'another_setting': 42,
            'dictionaries': dictionaries,
        }

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config_update):
        # Only 'dictionaries' can be changed.
        assert list(config_update.keys()) == ['dictionaries']
        self._config.update(config_update)


class DictCommandsTest(unittest.TestCase):

    def setUp(self):
        self.spanish = DictionaryConfig('spanish/main.json')
        self.english = DictionaryConfig('main.json')
        self.commands = DictionaryConfig('commands.json')
        self.user = DictionaryConfig('user.json')
        self.engine = FakeEngine([
            self.user,
            self.commands,
            self.english,
            self.spanish,
        ])

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


if __name__ == '__main__':
    unittest.main()
