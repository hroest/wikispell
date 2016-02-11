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

import re, sys
import string, codecs
import hunspell, webbrowser
import pickle
import wikipedia as pywikibot
import pagegenerators
import time

import xmlreader
import pagegenerators, catlib

# from spellcheck import SpecialTerm, distance, getalternatives, cap, uncap
# from spellcheck import removeHTML, Word, askAlternative
# from spellcheck import edit, endpage

from wikispell.SpellcheckLib import abstract_Spellchecker
from wikispell.SpellcheckLib import CallbackObject
from wikispell.SpellcheckLib import askAlternative
from wikispell.SpellcheckLib import Word, cap, uncap, edit, endpage
# from spellcheck import SpecialTerm, distance, getalternatives, cap, uncap

from wikispell.SpellcheckLib import InteractiveWordReplacer

hunspellEncoding = 'ISO-8859-15'

class RuleBasedWordAnalyzer():

    def __init__(self, minimal_word_size, multiple_occurence_tol, language,
                 stringent, common_words, composite_minlen):

        self.minimal_word_size = minimal_word_size
        self.multiple_occurence_tol = multiple_occurence_tol
        self.language = language
        self.common_words = common_words
        self.composite_minlen = composite_minlen
        self.stringent = stringent

    def skipWord(self, smallword, text, loc, use_alt):
        
        #  If hunspell doesn't know it, doesn't mean it is not correct
        #  This not only reduces the number of words considered to be
        #  incorrect but also makes it much faster since the feature
        #  hunspell.suggest takes most time (~6x speedup).

        if self.stringent > 1000:
            return False

        #  (a) - Remove common words and words that we found more than once
        #
        if smallword.lower() in self.common_words:
            return True

        if len(smallword) > 3 and \
          smallword[-1:] == 's' and smallword[:-1].lower() in self.common_words:
            return True
        
        #
        #  (b) - we check whether it is less than n characters long
        #
        if len(smallword) < self.minimal_word_size:
            return True

        if self.stringent > 500:
            return False

        #
        #  (c) - we check whether it is following an internal link like [[th]]is
        #
        if loc > 2 and text[loc-2:loc] == ']]':
            return True

        #
        #  (d) - skip if the word occurs more than n times in the text
        #
        if text.count(smallword) > self.multiple_occurence_tol:
            # print "found word", smallword.encode("utf8"), "multiple times:", text.count(smallword)
            return True

        #
        #  (e) - if it contains a number
        #
        if any(char.isdigit() for char in smallword) or \
           any(char in [")", "("] for char in smallword):
            return True

        #
        #  (f) - if it contains upper case letters after the first (abbreviation or something)
        #
        if len(smallword) > 2 and any(char.isupper() for char in smallword[1:]):
            return True

        #
        #  (g) - if it contains a TLD ending
        #
        if smallword.endswith(".ch") or smallword.endswith(".de") or \
           smallword.endswith(".com") or smallword.endswith(".at"):
            return True

        #
        #  (h) - remove some other stuff that is probably not a word in German or English
        #
        if any(char in [ "'", '"', "+", ".", "&", "@", ":" ] for char in smallword):
            return True

        if self.language in ["DE", "EN"] and any(char in [u"è", u"ê", u"é", u"ô", u"ò", u"ó", u"á", 
                                                           u"í"] for char in smallword):
            return True

        if self.language in ["EN"] and any(char in [u"ö", u"ä", u"ü"] for char in smallword):
            return True

        #
        #  (i) - return upon likely words
        #
        if self.language in ["DE"] and any([smallword.startswith(nr) for nr in [
            u"eins", u"zwei", u"drei", u"vier", u"fünf", u"sechs", u"sieben", u"acht", u"neun", u"zehn"]] ):
            # Likely a word in German
            return True

        #
        #  (j) skip composite words
        #
        if self.language == "EN":
            if smallword.startswith("de") and smallword[2:] in self.common_words:
                # print "EN can skip composite word", smallword.encode("utf8")
                return True
            if smallword.startswith("re") and smallword[2:] in self.common_words:
                # print "EN can skip composite word", smallword.encode("utf8")
                return True
            if smallword.endswith("ization") and smallword[:-7] in self.common_words:
                # print "EN can skip composite word", smallword.encode("utf8")
                return True

        if (self.language == "DE" or self.language == "EN") and self.stringent < 60:
            for i in range(2, len(smallword)):

                first_part = smallword[0:i].lower()

                if len(first_part) <= self.composite_minlen: 
                    continue

                if first_part in self.common_words:
                    other_part = smallword[i:].lower()

                    if self.language == "EN":
                        if other_part in ["ly"]:
                            # print "Skip English composite word ending with ly: ", smallword.encode("utf8")
                            return True
                        elif other_part in self.common_words:
                            # print "Skip English composite word", smallword[0:i].encode("utf8"), smallword[i:].encode("utf8")
                            return True

                    # We should not trust "endings" that are less than 3 characters long
                    #   Some of them are allowed in German, so we should explicitely include them
                    #  - see https://de.wikipedia.org/wiki/Deutsche_Deklination#Grunds.C3.A4tze 
                    #  - see https://de.wikipedia.org/wiki/Deutsche_Deklination#Starke_Deklination_der_Adjektive
                    elif len(other_part) < 3:
                        if other_part in ["n", "r", "s", "e", "en", "er",  "es", "em"]:
                            # print "Skip word according to German declension", smallword[0:i].encode("utf8"), "+", smallword[i:].encode("utf8")
                            return True

                        elif other_part in self.common_words:
                            # print "SPECIAL: strange ending!!!: ", "composite word", smallword[0:i].encode("utf8"), "+", smallword[i:].encode("utf8")
                            pass


                    elif self.language == "DE" and other_part in ["ern"]:
                        # print "SPECIAL: strange ending ern !!!: "
                        pass

                    elif len(other_part) <= self.composite_minlen:
                        continue

                    elif other_part in self.common_words:
                        # print "skip composite word", smallword[0:i].encode("utf8"), smallword[i:].encode("utf8")
                        return True

                    elif i +2 < len(smallword) and smallword[i:i+1] == "s" and len(first_part) > 2:
                        # potential "Fugenlaut" in German, see https://de.wikipedia.org/wiki/Fugenlaut
                        other_part = smallword[i+1:].lower()
                        if other_part in self.common_words:
                            # print "skip composite fugenlaut word", smallword[0:i].encode("utf8"), "+s+", smallword[i+1:].encode("utf8")
                            return True

                    # try composite word in German with 1-letter ending
                    elif self.language == "DE" and \
                            other_part[:len(other_part)-1] in self.common_words and \
                            len(first_part) > 2 and \
                            len(other_part) > 4 and \
                            other_part[len(other_part)-1:] in ["n", "r", "s", "e"]:
                        # print "SPECIAL: skip composite word (1 letter)", smallword[0:i].encode("utf8"), "+", smallword[i:].encode("utf8")
                        return True

                    # try composite word in German with 2-letter ending
                    elif self.language == "DE" and \
                            other_part[:len(other_part)-2] in self.common_words and \
                            len(first_part) > 2 and \
                            len(other_part) > 5 and \
                            other_part[len(other_part)-2:] in ["en", "er",  "es", "em"]:
                        # print "SPECIAL: skip composite word (2 letter)", smallword[0:i].encode("utf8"), "+", smallword[i:].encode("utf8")
                        return True

                    other_part = smallword[i:].lower()

        return False

class HunspellSpellchecker(abstract_Spellchecker):
    """
    Spellchecker class that uses hunspell as a backend

    There are a few parameters:
        - the minimal word size to be still checked (minimal_word_size)
        - the tolerance for multiple occurrences in the text word (if the word occurs more than multiple_occurence_tol times, it is considered correct)
        - whether to use the "suggestions" feature of hunspell 
    """

    def __init__(self, hunspell_dict, minimal_word_size = 3, 
                 multiple_occurence_tol = 1, nosuggestions=False, 
                 language="DE", stringent = 0, composite_minlen = 0, 
                 common_words = set([])):

        self._nosuggestions = nosuggestions
        self.correct_html_codes = False

        self._wordsWithoutSuggestions = []

        self.knownwords = {}

        self._unknown = []
        self._unknown_words = []

        self._replaceBy = {}
        self.stringent = stringent

        self._wordAnalyzer = RuleBasedWordAnalyzer(minimal_word_size, multiple_occurence_tol, language, stringent, common_words, composite_minlen)

        self._init_hunspell(hunspell_dict, language)

    def _init_hunspell(self, hunspell_dict, language):
        self.mysite = pywikibot.getSite()
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

    def spellcheck(self, text, forceAlternative=True):
        """Uses hunspell to replace wrongly written words in a given text.

        Returns the corrected text.
        """

        if self.correct_html_codes:
            text = removeHTML(text)

        loc = 0

        # Get ranges
        ranges = self.forbiddenRanges(text)
        ranges = sorted(ranges)
        curr_r = 0

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
                    if lratio < 0.7 or ldist > 5:
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

def run_bot(allPages, sp, pageStore=None):
    Callbacks = []
    stillSkip  = False;
    firstPage = True
    nonInteractive = True

    wr = InteractiveWordReplacer()
    # loadPagesWiki(wr, correctWords_page, ignorePages_page)
    output = ""

    if pageStore is None:
        nonInteractive = False

    UPDATE_EVERY = 10000
    # UPDATE_EVERY = 100
    update_nr = 1

    page_nr = 0
    for page in allPages:

        try:
            if not page.ns == '0': continue
            text = page.get()
            page_title = page.title
        except AttributeError:
            page_title = page.title()

        print "Performing spellcheck on page %s (%s pages processed so far)" % (page_title.encode("utf8"), page_nr)
        page_nr += 1

        st = time.time()
        try:
            text = page.get()
        except pywikibot.NoPage:
            pywikibot.output(u"%s doesn't exist, skip!" % page_title)
            continue
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"%s is a redirect, skip!" % page_title)
            continue

        # print "get pg time: ", time.time() - st

        st = time.time()
        orig_text = text

        text, wrongWords = sp.spellcheck(text)

        if not nonInteractive:
            text = sp.askUser(text, page_title)
        else:
            # print "got wrong words here", len(wrongWords)

            if page_nr % UPDATE_EVERY == 0:
                # print "put output", output
                curr_page = pageStore + str(update_nr)
                mypage = pywikibot.Page(pywikibot.getSite(), curr_page)
                mypage.put(output,  u'Update' )
                update_nr += 1
                output = ""

            # skip pages without wrong words ... 
            if len(wrongWords) == 0: 
                sp.clearCache()
                continue

            for w in wrongWords:

                # Skip specific words
                if page_title in wr.ignorePerPages and \
                   w.word in wr.ignorePerPages[page_title]: continue

                wrong = w.word
                wrong = w.derive()
                correct = ""
                correct = w.correctword

                if len(wrong) == 0:
                    continue
                if wrong.lower() == correct.lower():
                    continue
                
                if wrong[0].lower() != wrong[0] and len(correct) > 0:
                    # upper case
                    correct = correct[0].upper() + correct[1:]

                output += "{{User:HRoestTypo/V/Typo|%s|%s|%s}}\n" % (page_title, w.derive(), correct)

        sp.clearCache()

        # print "analysis time: ", time.time() - st

        if text == orig_text:
            continue

        pywikibot.output('\03{lightred}===========\nDifferences to commit:\n\03{default}');
        pywikibot.showDiff(orig_text, text)

        choice = pywikibot.inputChoice('Commit?', ['Yes', 'No'], ['y', 'n'])
        if choice == 'y':
            comment = "Fix typographical error"
            callb = CallbackObject()
            Callbacks.append(callb)
            page.put_async(text, comment=comment, callback=callb)

    for k, v in sp.knownwords.iteritems():
        print "* %s : %s" % (k,v)

def main():
    ###################################################################
    #                           MAIN                                  #
    ###################################################################
    title = []
    start = None
    newpages = False
    longpages = False
    rebuild = False
    category = None
    checklang = None
    dictionary = None
    common_words = None
    nosuggestions = False
    pageStore = None
    correct_html_codes = False
    xmlfile = False
    language = "DE"
    stringent = 0
    composite_minlen = 0
    for arg in pywikibot.handleArgs():
        if arg.startswith("-start:"):
            start = arg[7:]
        elif arg.startswith("-stringent:"):
            stringent = int(arg[11:])
        elif arg.startswith("-xmlfile:"):
            xmlfile = arg[9:]
        elif arg.startswith("-cat:"):
            category = arg[5:]
        elif arg.startswith("-dictionary:"):
            dictionary = arg[12:]
        elif arg.startswith("-newpages"):
            newpages = True
        elif arg.startswith("-common_words:"):
            common_words = arg[14:]
        elif arg.startswith("-longpages"):
            longpages = True
        elif arg.startswith("-minlen:"):
            composite_minlen = int(arg[8:])
            print "minlen", composite_minlen 
        elif arg.startswith("-nosugg"):
            nosuggestions = True
        elif arg.startswith("-language"):
            language = arg[10:]
        elif arg.startswith("-html"):
            correct_html_codes = True
        elif arg.startswith("-pageStore:"):
            pageStore = arg[11:]
        elif arg.startswith('-h') or arg.startswith('--help'):
            pywikibot.showHelp()
            return
        else:
            title.append(arg)
            print "title", arg

        # This is a purely interactive bot, we therefore do not want to put-throttle
        pywikibot.put_throttle.setDelay(1)

    if language not in ["DE", "EN"]:
        print "Language needs to be either DE or EN"
        return

    common_words_dict = set([])

    if True:
        if common_words is not None:
            f = open(common_words)
            for l in f:
                common_words_dict.add(l.strip().decode("utf8").lower())

        print "Got %s known good words from the supplied file" % len(common_words_dict)

    sp = HunspellSpellchecker(hunspell_dict = dictionary,
                              nosuggestions = nosuggestions,
                              minimal_word_size=4, 
                              common_words=common_words_dict,  
                              composite_minlen = composite_minlen,
                              language = language, stringent = stringent)
    sp.correct_html_codes = correct_html_codes
    sp.nosuggestions = nosuggestions

    if start:
        gen = pagegenerators.PreloadingGenerator(
            pagegenerators.AllpagesPageGenerator(start=start,includeredirects=False))
    elif xmlfile:
        gen = xmlreader.XmlDump(xmlfile).parse()
    elif newpages:
        def wrapper_gen():
            for (page, length) in pywikibot.getSite().newpages(500):
                yield page
        gen = wrapper_gen()
    elif longpages:
        def wrapper_gen():
            for (page, length) in pywikibot.getSite().longpages(500):
                yield page
        gen = wrapper_gen()
    elif len(title) != 0:
        title = ' '.join(title)
        gen = [pywikibot.Page(pywikibot.getSite(),title)]
    elif category:
        site = pywikibot.getSite()
        cat = catlib.Category(site, category)
        gen = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
    else:
        ####################################
        #Examples
        site = pywikibot.getSite()
        cat = catlib.Category(site,'Kategorie:Staat in Europa')
        cat = catlib.Category(site,'Kategorie:Schweizer')
        cgen = pagegenerators.CategorizedPageGenerator(cat)
        gen = pagegenerators.PreloadingGenerator(cgen)

    run_bot(gen, sp, pageStore=pageStore)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

