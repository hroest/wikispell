#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
This bot spellchecks Wikipedia pages using the hunspell spellcheck engine.  It
can be used in four ways:

spellcheck_hunspell.py Title
    Check a single page; after this the bot will ask whether you want to
    check another page
spellcheck._hunspellpy -start:Title
    Go through the wiki, starting at title 'Title'.
spellcheck_hunspell.py -newpages
    Go through the pages on [[Special:Newpages]]
spellcheck_hunspell.py -longpages
    Go through the pages on [[Special:Longpages]]

For each unknown word, you get a couple of options:
    numbered options: replace by known alternatives
    a: This word is correct; add it to the list of known words
    c: The uncapitalized form of this word is correct; add it
    i: Do not edit this word, but do also not add it to the list
    p: Do not edit this word, and consider it correct for this page only
    r: Replace the word, and add the replacement as a known alternative
    s: Replace the word, but do not add the replacement
    *: Edit the page using the gui
    g: Give a list of 'guessed' words, which are similar to the given one
    x: Ignore this word, and do not check the rest of the page

Command-line options:
-html          change HTML-entities like &uuml; into their respective letters.
               This is done both before and after the normal check.
-dictionary:   Location of the hunspell dictionary (-dictionary:/usr/share/hunspell/de_DE).
-common_words: Location of a file with common words

Example usage (you can find the dictionaries on https://github.com/hroest/spellcheck-data):

python spellcheck_hunspell.py  -dictionary:/usr/share/hunspell/de_DE -common_words:spellcheck-data/lists/de/common_15.dic  -language:DE  Schweiz

"""

"""
To install hunspell, you need to install the libhunspell as well as pyhunspell:
sudo apt-get install libhunspell-dev
wget http://pyhunspell.googlecode.com/files/hunspell-0.1.tar.gz
tar xzvf hunspell-0.1.tar.gz; cd hunspell-0.1/
sudo python setup.py install

# then you need to install the dictionaries in your language: 
sudo apt-get install hunspell-de-de-frami 
sudo apt-get install hunspell-de-ch-frami 

"""
#
# Distributed under the terms of the MIT license.
#

import re
import time
import hunspell

## pywikibot imports
try:
    import wikipedia as pywikibot
except ImportError:
    import pywikibot

# local imports
from Word import Word
from RuleBasedWordAnalyzer import RuleBasedWordAnalyzer
from SpellcheckLib import abstract_Spellchecker
from SpellcheckLib import askAlternative
from SpellcheckLib import cap, uncap, edit, endpage

hunspellEncoding = 'ISO-8859-15'

class HunspellSpellchecker(abstract_Spellchecker):
    """
    Spellchecker class that uses hunspell as a backend

    There are a few parameters:
        - the minimal word size to be still checked (minimal_word_size)
        - the tolerance for multiple occurrences in the text word (if the word
          occurs more than multiple_occurrence_tol times, it is considered
          correct)
        - whether to use the "suggestions" feature of hunspell 
    """

    def __init__(self, hunspell_dict, minimal_word_size = 3, 
                 multiple_occurrence_tol = 1, nosuggestions=False, 
                 language="DE", stringent = 0, composite_minlen = 0, 
                 remove_dissimilar = True,
                 common_words = set([]),
                 common_words_filter= set([])):

        self._nosuggestions = nosuggestions
        self.correct_html_codes = False

        self._wordsWithoutSuggestions = []

        self.knownwords = {}

        self._unknown = []
        self._unknown_words = []

        self._replaceBy = {}
        self.stringent = stringent
        self.remove_dissimilar = remove_dissimilar

        self._wordAnalyzer = RuleBasedWordAnalyzer(minimal_word_size,
                                                   multiple_occurrence_tol,
                                                   language,
                                                   stringent,
                                                   common_words,
                                                   common_words_filter,
                                                   composite_minlen)

        self._init_hunspell(hunspell_dict, language)

    def _init_hunspell(self, hunspell_dict, language):

        self.mysite = pywikibot.getSite()
        if hunspell_dict is None:
            raise Exception("Need to provide hunspell dictionary")

        self.hunspell = hunspell.HunSpell(hunspell_dict + ".dic", hunspell_dict + ".aff")
        self.hunspell_alternative = None
        if language == "DE":
            if hunspell_dict[-2:] == "DE":
                # Alternative for de is de_ch (swiss spellchecker)
                hunspell_alt = hunspell_dict[:-2] + "CH"
                import os.path
                if os.path.isfile(hunspell_alt + ".dic"):
                    self.hunspell_alternative = hunspell.HunSpell(hunspell_alt + ".dic", hunspell_alt + ".aff")
                else:
                    print "Cannot find alternative hunspell dictionary at", hunspell_alt + ".dic"
            else:
                # Guess some location
                hunspell_alt = "/usr/share/hunspell/de_CH"
                import os.path
                if os.path.isfile(hunspell_alt + ".dic"):
                    self.hunspell_alternative = hunspell.HunSpell(hunspell_alt + ".dic", hunspell_alt + ".aff")
                else:
                    print "Cannot find alternative hunspell dictionary at", hunspell_alt + ".dic"

        elif hunspell_dict[-2:] == "US":
            hunspell_alt = hunspell_dict[:-2] + "GB"
            import os.path
            if os.path.isfile(hunspell_alt + ".dic"):
                self.hunspell_alternative = hunspell.HunSpell(hunspell_alt + ".dic", hunspell_alt + ".aff")
                print "found alternative dictionary ....", hunspell_alt + ".dic"
            else:
                print "Cannot find alternative hunspell dictionary at", hunspell_alt + ".dic"

    def askUser(self, text, title):
        """Interactive part of the spellcheck() function.

        It uses the unknown words found before to make suggestions:

            - self._unknown_words
            - self._wordsWithoutSuggestions

        calls askAlternative to figure out what the user wants.
        """
        orig_len = len(text) +1 #plus one because of trailing \np
        for word in self._unknown_words:
            w = word.derive()
            if False and w in self._wordsWithoutSuggestions: pywikibot.output(u"\03{lightred}\"%s\"\03{default}" % w +
                u" skipped because no suggestions were found --> it is " +
                    u"assumed to be a name " );
            else:
                bigword = word
                sugg = bigword.suggestions
                loc = bigword.location
                # this should be right here, but we still have to search for it
                # if we changed the text then we need to account for that
                site = text.find( word.word , loc + len(text) - orig_len )

                LocAdd = len(word)
                if site == -1:
                    continue
                    # pywikibot.output(u"\03{lightred}error\03{default}, could " +
                    #                  "not find \"%s\" anymore" % w)
                    # continue
                replacement = askAlternative(bigword, knownwords=self.knownwords,
                                             title=title,
                                             replaceBy=self._replaceBy,
                                             context=text[max(0,site-55):site+len(w)+55], 
                                             correct_html_codes=self.correct_html_codes)

                if replacement == edit:
                    newtxt = self.saveEditArticle(text, jumpIndex = 0, highlight = w)
                    if newtxt:
                        text = newtxt
                elif replacement == endpage:
                    break
                else:
                    replacement = word.replace(replacement)
                    text = text[:site] + replacement + text[site+LocAdd:]
        return text

    def saveEditArticle(self, text, jumpIndex = 0, highlight = ''):
        """Edits an article safely.

        Tries to edit articles safely - some gothic characters cause problems
        and raise a value error which then causes the whole program to crash.
        Here we catch those exceptions and deal with them.
        """
        import editarticle
        editor = editarticle.TextEditor()
        try:
            newtxt = editor.edit(text, jumpIndex = jumpIndex, highlight = highlight)
        except ValueError:
            #now we try without the last couple of chars
            #this is a hack to find out where to cut since we are
            #probably dealing with IW links
            if not text.find('[[Kategorie:') == -1: cut = text.find('[[Kategorie:')
            elif not text.find('[[en:') == -1: cut = text.find('[[en:') == -1
            else: cut = len(text) -600
            try:
                newtxt = editor.edit(text[:cut], jumpIndex = jumpIndex, highlight = highlight)
                newtxt = newtxt + text[cut:]
            except ValueError:
                pywikibot.output(u"\03{lightred}There are unprintable character" +
                     "in the text, I cannot edit, try something" +
                     "different\03{default}");
                return text
        if newtxt:
            return newtxt
        else:
            return text

    def spellcheck(self, text, forceAlternative=True, level="full"):
        """Uses hunspell to replace wrongly written words in a given text.

        level controls how much text should be excluded from spellchecking:
            - full: exclude as much as possible

        Returns the corrected text.
        """

        if self.correct_html_codes:
            text = removeHTML(text)

        # Get ranges
        loc = 0
        curr_r = 0
        ranges = self.forbiddenRanges(text, level=level)

        # Check whether to use alternative spellchecker (e.g. swiss)
        schweiz_search = "<!--schweizbezogen-->"
        match = re.search(schweiz_search, text)
        useCH = False
        if match or forceAlternative:
            useCH = True

        # For bookkeeping
        self.time_suggesting = 0
        self.totalWordsChecked = 0
        self.checkWords = 0
        starttime = time.time()

        # Wordsearch using regex
        wordsearch = re.compile(r'([\s\=\<\>\_]*)([^\s\=\<\>\_/\-]+)')

        nr_words = 0
        wrongWords = []
        while True:

            match = wordsearch.search(text, loc)
            LocAdd = 0
            if not match and False:
                # No more words on this page
                print "=" * 75
                print "Time suggesting %0.4f s" % self.time_suggesting
                print "Total time %0.4f s" % (time.time() - starttime)
                print "----------------------"
                print "Time suggesting of total time %0.4f%% " % (
                    self.time_suggesting *100.0 / (time.time() - starttime) )
                print "Number of words", nr_words
            if not match:
                break

            curr_r, loc, in_nontext = self.check_in_ranges(
                ranges, match.start(), match.end(), curr_r, loc)
            if in_nontext:
                continue

            nr_words += 1
            # Split the words up at special places like &nbsp; or – (these will
            # usually not be found in the dictionary)
            spl = re.split('&nbsp;', match.group(2))
            if len(spl) >1: LocAdd = 5
            elif len(spl) == 1:
                spl = re.split(u'–', spl[0])
            ww = spl[0]
            LocAdd += len(ww)+1
            bigword = Word(ww)
            smallword = bigword.derive()

            loc += len(match.group(1))

            w = self._spellcheck_word(text, smallword, bigword, ww, loc, LocAdd, useCH)
            if w is not None:
                wrongWords.append(w)

            # proceed to the next location
            loc += LocAdd

        # We are done with all words
        if self.correct_html_codes:
            text = removeHTML(text)

        return text, wrongWords

    def _spellcheck_word(self, text, smallword, bigword, ww, loc, LocAdd, use_alt):
        """ Spellcheck a single word

                self._unknown_words.append(bigword);
        """

        done = False

        try:
            smallword_encoded = smallword.encode(hunspellEncoding)
        except UnicodeEncodeError as s: 
            # There are some unicode characters that we cannot render in ISO
            # 8859 and these will throw an error here.
            # Nothing left to do ...
            return

        smallword_utf8 = smallword.encode('utf8')
        smallword_utf8_prev = text[loc:loc+1].encode('utf8') + smallword_utf8
        smallword_utf8_next = smallword_utf8 + text[loc+LocAdd-1:loc+LocAdd].encode('utf8')

        if not smallword == '' and not smallword.isupper() and \
           not self._check_with_hunspell(smallword_encoded, use_alt):

            self.totalWordsChecked += 1

            inWW = ww.find(smallword)
            if not inWW == 0:
                smallword_utf8_prev = ww[inWW].encode('utf8') + smallword_utf8
            if not inWW+len(smallword) >= len(ww):
                smallword_utf8_next = smallword_utf8 + ww[inWW+len(smallword)].encode('utf8')

            #
            #  - if we found it more than once, its probably correct
            #
            if smallword in self._unknown:
                self._unknown.remove(smallword)
                return 

            #
            #  - if the word has been marked as known by the user, it is correct
            #
            if smallword in self.knownwords:
                return

            if self._wordAnalyzer.skipWord(smallword, text, loc, use_alt):
                return

            #  now we need to get the suggestions from hunspell. This takes
            #  nearly all time
            if True:
                self.checkWords += 1
                pywikibot.output(u"%s.\03{lightred}\"%s\"\03{default} -> get Suggestions" % (
                    self.checkWords, smallword));
                t1 = time.time()
                if self._nosuggestions:
                    sugg = []
                elif use_alt and self.hunspell_alternative is not None:
                    sugg = self.hunspell_alternative.suggest(smallword_utf8)
                else:
                   sugg = self.hunspell.suggest(smallword_utf8)
                self.time_suggesting += time.time() -t1

                if not self._nosuggestions \
                    and len(sugg) == 0 \
                    and not smallword in self._wordsWithoutSuggestions:
                    self._wordsWithoutSuggestions.append(smallword)

                #  go through the suggestions and see whether our word matches
                #  some derivative.
                for i in range(len(sugg)):
                    try:
                        sugg[i] = unicode(sugg[i], 'utf-8')
                    except UnicodeDecodeError:
                        sugg[i] = unicode(sugg[i], 'iso8859-1')
                    if sugg[i] == smallword:
                        done = True

                if len(sugg) > 0:
                    bigword.correctword = sugg[0]
                else:
                    bigword.correctword = u""

            #######################################################
            #So now we know whether we have found the word or not #
            #######################################################
            if not done:
                bigword.suggestions = sugg
                bigword.location = loc

                try:
                    import Levenshtein

                    lratio = Levenshtein.ratio(bigword.correctword, smallword)
                    ldist = Levenshtein.distance(bigword.correctword, smallword)
                    if self.remove_dissimilar and (lratio < 0.7 or ldist > 5):
                        return

                except ImportError:
                    pass

                self._unknown.append(smallword);
                self._unknown_words.append(bigword);
                return bigword

        return 

    def clearCache(self):
        """
        Clears cache and prepares for a new page
        """

        self._unknown_words = []
        self._unknown = []
        self._wordsWithoutSuggestions = []

    def _check_with_hunspell(self, word, useAlternative):
        return self.hunspell.spell(word) or \
                (useAlternative and self.hunspell_alternative is not None 
                 and self.hunspell_alternative.spell(word)) 

