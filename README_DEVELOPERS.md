Hacking
------

Scripts
------

There are three executable scripts available which correspond to the
functionality described in the README.md file.

    spellcheck_hunspell.py
    spellcheck_wordfrequency.py
    spellcheck_wordlist.py


Library
-------

The library contains a set of files

## Main library 

The library file contains askAlternative to interactively ask users for
alternative words and read in data files.

    SpellcheckLib.py

The abstract spellchecker file contains the abstract_Spellchecker class, the
base class for many of the spell checkers.  It contains the ability to identify
ranges in text that should be excluded

    AbstractSpellchecker.py

## Individual spellcheckers

The blacklisting spellchecker which uses a list of "known wrong" words and is
implemented in the following class:

    BlacklistSpellchecker.py

The spellchecker used by the hunspell script is implemented in the following
classes. It uses the the RuleBasedWordAnalyzer which implements a set of rules
to filter the reported words and remove false positives

    HunspellSpellchecker.py
    RuleBasedWordAnalyzer.py

The WordFrequencyChecker contains the classes used by the word frequency
analyzer.

    WordFrequencyChecker.py

## Shared classes

Used by all scripts to interactively replace words, contains the
InteractiveWordReplacer and InteractiveSearchReplacer. The latter uses a simple
search and replace strategy on the whole text while the former

    InteractiveWordReplacer.py

A class which can read a permanent list of words from wikipedia pages that
contain information about which words not to replace

    PermanentWordlist.py


## Text parsing and helper classes

text parsing

    textrange_parser.py

a few helper classes

    Callback.py
    Word.py

Testing
-------

To run all the tests, run

    py.test tests/

