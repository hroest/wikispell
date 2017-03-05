WikiSpell
---------

This package provides a library and a set of scripts designed to spellcheck
pages on Wikipedia. It uses the pywikibot project to interface with Mediawiki
projects.

Hacking
-------

Please read the [developers file](README_DEVELOPERS.md).

Install
-------

## Dependencies

Part of these scripts rely on libhunspell and pyhunspell. To install on an
Ubuntu system, first install libhunspell

        sudo apt-get install libhunspell-dev

Download the Python bindings from https://pypi.python.org/pypi/hunspell and install with

        sudo python setup.py install

Then you need to install the dictionaries in your language:

        sudo apt-get install hunspell-en-us
        sudo apt-get install hunspell-de-de-frami
        sudo apt-get install hunspell-de-ch-frami

Secondly, install the pywikibot

git clone https://github.com/wikimedia/pywikibot-compat.git

and add it to your PYTHONPATH

## Install this software

Simply clone it from github and run the scripts (make sure that pywikibot and
pyhunspell are installed and in your PYTHONPATH).

Usage
-----

## Spellchecking

This script uses the popular hunspell spellchecker to check the spelling of one
or more Wikipedia pages. This identifies each word and runs it against the
hunspell spellchecker, reporting misspelled words (or unknown words).

    spellcheck_hunspell.py -dictionary:/usr/share/hunspell/de_DE Title

Note that you need to install libhunspell as well as pyhunspell.  You need to
use -dictionary: to pass the location of a hunspell dictionary.

Also, it helps if you supply a set of common words with the `-common_words:`
flag, which is a text file containing one word per line that should not be
considered incorrect. One good start for such a list of words is the
https://github.com/hroest/spellcheck-data repository which contains spellcheck
files for German and English. It works well to exclude words here that occur at
least n times in the Wikipedia, those that occur in the title of articles (in
multiple languages). Also, additional wordlists can be added.

There are a few parameters to tune the output, the first one is the amount of
text that should be excluded from the checking (using the `-excludeText:` flag).
Possible parameters are

* none: check all text
* relaxed: remove most common offenders, such as templates, comments, tables, bold and italic text
* wiki-skip: remove all Wiki markup, including references
* full: remove as much text as possible including text in quotation marks, lists, after weblink section etc

The more text you exclude, the higher the likelihood to miss a few wrong words
as they never get checked. However, if you do chose to turn off this feature
(using `-excludeText:none`), then you will loose a lot of the benefits of the
syntax-aware parsing this script does.

Another important parameter is the aggressiveness of the heuristics that remove
potential false positives from the output. This value is an integer between 0
and 1000, using `-stringent:1000` turns off all heuristics. Finally, using
`-keepDissimilar` will allow you to not discard words for which hunspell could
not find a suitable suggestion (often these words are names of people and
places).

Using these parameters in combination can reduce the number of words that need
to be checked by a factor of 20-fold or more, thus substantially reducing false
positives. Naturally, some wrongly spelled word may also get excluded by these
filters, so use at your own discretion.

## Wordlist

It is often more convenient to work with known false words than trying to
spellcheck all of Wikipedia. This is the idea behind the second approach which
lets you check individual words or a list of words against Wikipedia.

You can replace a single word in all of Wikipedia page

    python spellcheck_wordlist.py -searchWiki -singleword:"Dölli;test"

Or you can replace it only on a single page

    python spellcheck_wordlist.py Uttwil -singleword:"goldschmied;test"

If you have a given list of (known false) words, you can check them against Wikipedia

    python spellcheck_wordlist.py -blacklist:perturbations.dic -searchWiki
    python spellcheck_wordlist.py -blacklist:perturbations.dic -recentchanges
    python spellcheck_wordlist.py -blacklistpage:User:HRoestTypo/replacedDerivatives -cat:Schweiz
    python spellcheck_wordlist.py -blacklistpage:User:HRoestTypo/replacedDerivatives -searchWiki
    python spellcheck_wordlist.py -blacklistpage:User:HRoestTypo/replaced -searchWiki

Where the words can also be derived from a Wikipedia page themselves instead of
a local text file. A set of potentially wrong words can be found at
https://github.com/hroest/spellcheck-data which contains lists of common words
that were perturbed as well as code to create such lists.

If you have a Wikipedia page with a set of false words and associated pages
(e.g. if you already found the words and pages), you use this script to
interactively replace them:

    python spellcheck_wordlist.py -typopage:User:HRoestTypo/ExamplePage
    python spellcheck_wordlist.py -typofile:alocalfile.txt

These typopages can be generated by using -non-interactive and -pageStore.

Using an XML file is also possible (instead of the online version)

    python spellcheck_wordlist.py -xmlfile:/path/to/dewiki-latest-pages-articles.xml.bz2 -singleword:"und;test" -batchNr:10

## Word frequency

Given a database with words and their frequencies in Wikipedia, the following
script will iterate through the most common words and for each common word
identify similar words that occur with very low frequency and are thus likely
misspellings of the more common word. The low frequency words are then searched
in Wikipedia and replaced with the correct word.

        python spellcheck_wordfrequency.py  --db wikiwords.countedwords_20161020

This will read the MySQL database `wikiwords.countedwords_20161020` and use the
stored word frequencies in it.

