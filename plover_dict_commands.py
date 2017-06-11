#!/usr/bin/env python

import atexit
import json
import os

from plover.config import DictionaryConfig
from plover.oslayer.config import CONFIG_DIR

# Helpers. {{{

def match_dictionary(path, dictionaries):
    normalized_path = os.path.normpath(path)
    matches = [
        (len(d.short_path), n)
        for n, d in enumerate(dictionaries)
        if (os.sep + d.short_path).endswith(os.sep + normalized_path)
    ]
    if not matches:
        raise ValueError('No dictionary matching %r found.' % path)
    matches.sort()
    return matches[0][1]

def prioritize_dictionaries(selections, dictionaries):
    dictionaries = dictionaries[:]
    for path in reversed(selections):
        m = match_dictionary(path, dictionaries)
        d = dictionaries.pop(m)
        dictionaries.insert(0, d)
    return dictionaries

def toggle_dictionaries(selections, dictionaries):
    dictionaries = dictionaries[:]
    for s in selections:
        toggle = s[0]
        path = s[1:]
        if not toggle in '-+!':
            raise ValueError('Invalid dictionary toggle: %r.' % toggle)
        m = match_dictionary(path, dictionaries)
        d = dictionaries[m]
        if toggle == '+':
            enabled = True
        elif toggle == '-':
            enabled = False
        elif toggle == '!':
            enabled = not d.enabled
        dictionaries[m] = d.replace(enabled=enabled)
    return dictionaries


BACKUP_DICTIONARY_PATH = os.path.join(CONFIG_DIR, "solo_mode_dictionary_backup.json")

PREVIOUS_DICTIONARIES = 0
SOLO_ENABLED = 1
SOLO_DICT_HAS_RUN = 2
solo_state = [[], False, False]

# solo_dict safety guards, restores old dictionary stack state if Plover is closed
# before exiting the temporary mode.

def load_dictionary_stack_from_backup(path):
    try:
        with open(path, 'r') as f:
            dictionaries = json.load(f)
        if dictionaries:
            old_dictionaries = [DictionaryConfig(x[0], x[1]) for x in dictionaries]
            os.remove(BACKUP_DICTIONARY_PATH) #backup recovered, delete file
            return old_dictionaries
        else:
            return None
    except IOError:
        # No backup file, no problem
        return None

def backup_dictionary_stack(dictionaries, path):
    if dictionaries:
        with open(path, 'w') as f:
            json.dump(dictionaries, f)
    else:
        try:
            os.remove(path)
        except OSError:
            pass #Good, we didn't want it anyway!

def toggle_solo_dictionaries(selections, engine_dictionaries):
    # Load persisted dictionaries from last time Plover was open,
    # if applicable.
    if not solo_state[SOLO_DICT_HAS_RUN]:
        solo_state[SOLO_DICT_HAS_RUN] = True
        persisted_dictionaries = load_dictionary_stack_from_backup(BACKUP_DICTIONARY_PATH)
        if persisted_dictionaries:
            solo_state[PREVIOUS_DICTIONARIES] = persisted_dictionaries 
            solo_state[SOLO_ENABLED] = True

    if solo_state[SOLO_ENABLED]:
        solo_dictionaries = engine_dictionaries[:]
    else:
        solo_state[PREVIOUS_DICTIONARIES] = engine_dictionaries[:]
        backup_dictionary_stack(solo_state[PREVIOUS_DICTIONARIES], BACKUP_DICTIONARY_PATH)
        solo_state[SOLO_ENABLED] = True
        solo_dictionaries = engine_dictionaries[:]
        for i, d in enumerate(solo_dictionaries):
            solo_dictionaries[i] = d.replace(enabled=False)

    solo_dictionaries = toggle_dictionaries(selections, solo_dictionaries)
    return solo_dictionaries

def restore_dictionaries_after_solo():
    solo_state[SOLO_ENABLED] = False
    if solo_state[SOLO_DICT_HAS_RUN]:
        previous_dictionaries = solo_state[PREVIOUS_DICTIONARIES]
    else:
        # We're disabling a temporary mode before enabling one? See if there's
        # a backup dictionary stack from last Plover session before clobbering
        # the user's normal dictionary state.
        backed_up_dictionaries = load_dictionary_stack_from_backup(BACKUP_DICTIONARY_PATH)
        if backed_up_dictionaries:
            previous_dictionaries = backed_up_dictionaries
        else:
            previous_dictionaries = None
        
    solo_state[PREVIOUS_DICTIONARIES] = []
    return previous_dictionaries

# }}}

# Commands. {{{

def priority_dict(engine, cmdline):
    selections = [path.strip() for path in cmdline.split(',')]
    dictionaries = engine.config['dictionaries']
    dictionaries = prioritize_dictionaries(selections, dictionaries)
    engine.config = { 'dictionaries': dictionaries }

def toggle_dict(engine, cmdline):
    selections = [path.strip() for path in cmdline.split(',')]
    dictionaries = engine.config['dictionaries']
    dictionaries = toggle_dictionaries(selections, dictionaries)
    engine.config = { 'dictionaries': dictionaries }

def solo_dict(engine, cmdline):
    selections = [path.strip() for path in cmdline.split(',')]
    dictionaries = engine.config['dictionaries']
    dictionaries = toggle_solo_dictionaries(selections, dictionaries)
    engine.config = { 'dictionaries': dictionaries }

def end_solo_dict(engine, cmdline):
    restored_dictionaries = restore_dictionaries_after_solo()
    if restored_dictionaries:
        engine.config = { 'dictionaries': restored_dictionaries }
    backup_dictionary_stack(None, BACKUP_DICTIONARY_PATH)
# }}}
