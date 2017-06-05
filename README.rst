Plover Dict Commands
====================

*Plugin for enabling, disabling, and changing the priority of dictionaries in Plover.*

**PRIORITY_DICT**

``{PLOVER:PRIORITY_DICT:dict1.json,dict2.json,...}``

Moves selected dictionaries to the top of the dictionary stack.


**TOGGLE_DICT**

``{PLOVER:TOGGLE_DICT:+dict1.json,-dict2.json,!dict3.json}``

Turns dictionaries on or off entirely. Each dictionary is prepended with a control symbol:

    \+    enables a dictionary

    \-    disables a dictionary

    !    toggles a dictionary


**SOLO_DICT and END_SOLO_DICT**

``{PLOVER:SOLO_DICT:+dict1.json...}``

``{PLOVER:END_SOLO_DICT}``

For temporarily toggling a new list of dictionaries without affecting the old
dictionary stack. Uses the same control symbols as TOGGLE_DICT,
though if the mode itself does not need to toggle its own dictionaries,
using only the + to enable dictionaries should be sufficient because
the SOLO_DICT command starts with a clean slate of disabled dictionaries.

``END_SOLO_DICT`` restores the dictionary stack to its original state before
a ``SOLO_DICT`` command. Together these two commands are convenient for entering and exiting temporary modes without unexpected interference
from multistroke entries in lower priority dictionaries.

**Example: Safe temporary modes for programs such as vim**

To keep vim normal mode predictable and not trigger unexpected strings of
commands if Plover sends vim a whole word worth of keystrokes, potential
interference from other dictionaries must be prevented and the display of
untranslated strokes must be suppressed.

Suppressing untranslated strokes can be done with a very simple python
dictionary at the lowest priority of the dictionary stack that translates
anything that reaches it into "{null}".

.. code:: python

    #suppress_untranslates.py

    LONGESTKEY = 1
    def stroke(key):
        return "{null}"

Loading python dictionaries requires installing the follow plugin:

https://github.com/benoit-pierre/plover_python_dictionary

Sample dictionary entry for exiting vim's insert mode and enabling the command dictionary:

``"SREFBG":"{^}{#Escape}{PLOVER:SOLO_DICT:+vim_navigation.json,+suppress_untranslates.py}``

To get back out of the mode and put vim back in insert mode, vim_navigation.json needs
one of these definitions:

``"STPHERT":"{PLOVER:END_SOLO_DICT}{^}{#i}"``

The same pattern (minus enabling an untranslate suppression dictionary) can be used for temporarily comparing theories or enabling a dictionary for another language.
