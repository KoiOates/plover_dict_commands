#!/usr/bin/env python

import os


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

# }}}
