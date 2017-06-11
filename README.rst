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

SOLO_DICT backs up your old dictionary stack to a file in your plover configuration directory.
If you quit Plover while a SOLO_DICT mode is enabled, using an END_SOLO_DICT stroke will set
it back to normal.

**Safe temporary modes for programs such as vim**

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

**Language toggling**

Which way to switch between languages is easiest depends on how many dictionaries you use at
once and how often you plan to change your default dictionary setup.

For a short and rarely changing list of dictionaries, a toggle stroke that deals with all
the dictionaries of both languages is easily done.

``"THROLG":"{PLOVER:TOGGLE_DICT:!spanish/main.json,!spanish/user.json,!english/main.json,!english/user.json}"``

In this case, dictionaries that are not language specific, like for navigation and commands,
can be left alone.

If you have a long or frequently changing list of dictionaries, a command like the previous one would
have to be updated often to avoid unpredictable behavior. If a new dictionary of a language you're not
using is active, even at a lower priority, you will likely have single stroke words in one language
turn into multistroke words in the other language from time to time. It may be easier in this case
to trigger a secondary set of language dictionaries as a temporary mode as in the vim example
because it will continue to work if you add or remove dictionaries in the primary language.

Because SOLO_DICT starts with a clean slate, be sure to include any navigation/command dictionaries
you want to use while writing in the other language in the list of enabled dictionaries passed to
SOLO_DICT.

``"SPAELG":"{PLOVER:SOLO_DICT:+spanish/main.json,+spanish/user.json,+commands.json}"``

And in one of the activated dictionaries, have an END_SOLO_DICT definition to restore your previous
set of dictionaries.

``"SPWHRAPBG":"{PLOVER:END_SOLO_DICT}"``
