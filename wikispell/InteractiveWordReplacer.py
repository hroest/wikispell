#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
A library of spellchecking helper classes and functions
"""

#
# Distributed under the terms of the MIT license.
#

import time, sys

# local imports
from Word import Word
from AbstractSpellchecker import abstract_Spellchecker
from wikispell.PermanentWordlist import PermanentWordlist
from Callback import CallbackObject
import textrange_parser as ranges

## pywikibot imports
try:
    import wikipedia as pywikibot
    import pagegenerators
except ImportError:
    import pywikibot
    from pywikibot import pagegenerators

class InteractiveWordReplacer(abstract_Spellchecker):
    """ Interactively replace individual words

    The main function is processWrongWordsInteractively which takes a list of
    page objects, each of which has a list of "WrongWord" objects attached to
    it. These objects describe which words need to be replaced on the page in
    question.
    """

    def __init__(self, xmldump=None, pm=None):
        self.ignorePages = []

        self.Callbacks = []

        if pm is None:
            pm = PermanentWordlist(None)

        self.pm = pm

    def processWrongWordsInteractively(self, pages, offline=False, reloadPages=False):
        """This will process pages with wrong words.

        It expects a list of pages with words attached to it.


        Args:
            pages(list(pywikibot.Page)) : The Wikipedia pages
            reloadPages(boolean) : Whether to reload all pages (otherwise assumes they are loaded already)
        Note that each pywikibot.Page is expected to have a list of
        wikispell.WrongWord attached to it in a variable called "words" which
        are the wrongly spelled words.

        Returns:
            None
        """

        self.performReplacementList = []
        ask = True
        if reloadPages:
            pages = pagegenerators.PreloadingGenerator(pages)

        for page in pages:
            print('Processing Page = %s'% page.title() )
            thisReplace = []
            try:
                text = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist, skip!" % page.title())
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, get target!" % page.title())
                oldpage = page
                page = page.getRedirectTarget()
                page.words = oldpage.words
                text = page.get()

            text = page.get()
            self._checkSpellingInteractive(page)
            newtext = self._doReplacement(text, page)

            if text == newtext: 
                continue

            pywikibot.showDiff(text, newtext)
            choice = pywikibot.inputChoice('Commit?', ['Yes', 'yes', 'No', 'no'], ['y', '\\', 'n', ']'])

            if choice in ('y', '\\'):
                callb = CallbackObject()
                self.Callbacks.append(callb)
                page.put_async(newtext, comment=page.typocomment, callback=callb)

    def _checkSpellingInteractive(self, page):
        """Interactively goes through all wrong words in a page.

        All we do here is save doReplace = True if we want to replace it, while
        doReplace will do the actual replacement.
        """

        title = page.title()
        text = page.get()
        words = page.words
        for w in words: 
            w.doReplace = False

        # Go through all wrong words in this page
        for w in words:
            smallword = w.word

            # Check if on ignore list -> continue
            if self.pm.checkIsIgnored(title, smallword):
                continue

            bigword = Word(w.bigword)
            loc = w.location

            # Try to find replacement site
            w.site = text.find(bigword.word, loc)
            if w.site == -1: 
                w.site = text.find(bigword.word)
            if w.site == -1: 
                pywikibot.output(u"Not found any more in %s: %s" % (
                title, bigword.word))
                continue

            # We now have a potential site for replacement
            sugg = w.correctword
            w.LocAdd = len(bigword)

            # Check if the word has been replaced in the meantime with the
            # correct suggestion
            if len(text) > loc + len(sugg) and \
              text[w.site:w.site+len(sugg)].lower() == sugg.lower():
                continue
            if smallword == sugg: 
                continue

            # Adjust case
            if smallword[0].isupper(): 
                sugg = sugg[0].upper() + sugg[1:]

            # Print the two words
            pywikibot.output(u"Replace \03{lightred}\"%s\"" % smallword +
              "\03{default} \nby      \03{lightgreen}\"%s\"\03{default}" % sugg)

            # Print context
            pywikibot.output(u"    %s" % text[max(0,w.site-55):w.site+len(w)+55])
            choice = pywikibot.inputChoice('', ['Yes', 'yes', 'No', 'no',
               'No but dont save', 'never replace' 'Replace by something else',
                'Exit and go to next site'], ['y', '\\', 'n', ']', 'b', 'v', 'r', 'x'])

            # Evaluate user choice
            if choice == 'b':
                continue
            if choice in ('v'): 
                self.pm.markCorrectWord(smallword)
                continue
            if choice in ('n', ']'): 
                self.pm.markCorrectWordPerPage(title, smallword)
                continue
            if choice == 'x': 
                return
            if choice == 'r':
                w.replacement = pywikibot.input(u"What should I replace \"%s\" by?"
                                              % bigword.word)
                w.doReplace = True

            if choice in ( 'y','\\'):
                w.replacement = bigword.replace(sugg)
                w.doReplace = True

                self.pm.markReplaced(smallword, sugg)

    def _doReplacement(self, text, page, ask = True):
        """This will perform the replacement for one page and return the text.
        """

        page.typocomment  = u"Tippfehler entfernt: "

        #now we have the text, lets replace the word
        for i, word in enumerate(page.words):
            if not word.doReplace: 
                continue

            self.performReplacementList.append(word)

            # Try to find replacement site (text may have changed in the meantime)
            site = text.find( word.bigword, word.site )
            if site == -1:
                site = text.find( word.bigword )
            if site == -1: 
                continue

            # now we have the site (page might be changed in meantime)
            loc = site
            replacement = word.replacement
            LocAdd = word.LocAdd

            # Check for cases where the the wrong word is contained in the
            # replacement but already corrected (this may happen if somebody
            # has replaced the text in the meantime). 
            # We would still find the wrong word but should not replace it!
            replacementHere = text.find( replacement )
            while not replacementHere == site and not replacementHere == -1:
                replacementHere = text.find( replacement , replacementHere+1)

            # exclude cases where replacement is contained in wrong word
            if replacementHere == site and word.bigword.find(replacement) == -1:
                continue

            # Replace the text
            text = text[:loc] + replacement + text[loc+LocAdd:]

            if i > 0: 
                page.typocomment += " , "
            page.typocomment += word.word + " => " + word.replacement

        return text

class InteractiveSearchReplacer(abstract_Spellchecker):
    """ Interactively replace individual words using search and replace

    Use the checkit function to replace words
    """

    def __init__(self, pm=None):

        self.pm = pm

    def checkit(self, pages, wrongs, g_correct, interactive=True):
        """
        Interactively replaces a set of wrongly written words in multiple pages with a correct one.

        Takes a list of pages and associated wrong words and goes through them
        one by one, asking user input to correct it.  Assumes that there is a
        single correct word for all the pages.

        Args:
            pages(list(pywikibot.Page)) : The Wikipedia pages
            wrongs(list(string) : The list of wrong words (one for each page)
            g_correct(string) : The correct word (the same for all pages)
            interactive(boolean) : Whether to run interactively

        Returns:
            string : Returns output in non-interactive mode that can be stored and processed later
        """

        output = ""
        for i,page in enumerate(pages):
            wrong = wrongs[i]
            correct = g_correct
            if wrong in self.pm.getReplaceDict():
                correct = self.pm.getReplaceDict()[wrong]

            print "Starting work on", page.title(), "word:", wrong

            if self.pm.checkIsIgnored(None, wrong.lower()):
                print "    Continue (word in ignore)"
                continue

            try:
                text = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist, skip!" % page.title())
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, get target!" % page.title())
                page = page.getRedirectTarget()
                text = page.get()

            myranges = self.forbiddenRanges(text, level="moderate")
            r = ranges.Ranges()
            r.ranges = myranges
            ext_r = r.get_large_ranges()

            wupper = wrong[0].upper() + wrong[1:]
            wlower = wrong[0].lower() + wrong[1:]
            cupper = correct[0].upper() + correct[1:]
            clower = correct[0].lower() + correct[1:]

            # Try to find the position to replace the word
            #  -> first look for the upper case version of the word
            pos = 0 
            newtext = text[:]
            while True:
                found = newtext.find(wupper, pos)
                pos += found + 1
                if found in ext_r and found != -1:
                    # Skip excluded position
                    continue
                if found == -1:
                    break
                newtext = newtext[:found] + cupper + newtext[found+len(wupper):]

            # -> next look for the lower case version of the word
            mywrong = wupper
            if newtext == text: 
                pos = 0 
                newtext = text[:]
                while True: 
                    found = newtext.find( wlower, pos)
                    pos += found + 1
                    if found in ext_r and found != -1:
                        # Skip excluded position
                        continue
                    if found == -1:
                        break
                    newtext = newtext[:found] + clower + newtext[found+len(wlower):]

                mywrong = wlower
                if newtext == text:
                        print "    Continue (no change)"
                        continue

            if not interactive:
                output += "{{User:HRoestTypo/V/Typo|%s|%s|%s}}\n" % (page.title(), wrong, correct)
                continue

            pywikibot.showDiff(text, newtext)
            a = self._ask_user_input(page, mywrong, correct, newtext, text)
            if a is not None and a == "x":
                print "Exit, go to next"
                return

        return output

    def _ask_user_input(self, page, wrong, correct, newtext, text):
        """
        Takes a page and a list of words to replace and asks the user for each one
        """
        mynewtext = newtext
        mycomment = "Tippfehler entfernt: %s -> %s" % (wrong, correct) 
        correctmark = False
        while True:
            choice = pywikibot.inputChoice('Commit?', 
               ['Yes', 'yes', 'No', 'no', 'Yes to all', 'No to all', 
                'replace with ...', 'replace always with ...', '<--!sic!-->', "Exit"],
                           ['y', '\\', 'n', ']', 'a', 'noall', 'r', 'ra', 's', 'x'])

            if choice == 'noall':
                print 'no to all'
                self.pm.markCorrectWord(wrong.lower() )
                return None

            elif choice in ('y', '\\'):

                # Check for correctmark (correct a word often written wrongly "sic")
                if not correctmark:
                    self.pm.markReplaced(wrong, correct)

                # TODO : return new text rather than put
                page.put_async(mynewtext, comment=mycomment)
                return None

            elif choice == 's':
                mynewtext = text.replace(wrong, wrong + '<!--sic!-->')
                pywikibot.showDiff(text, mynewtext)
                mycomment = "Korrektschreibweise eines oft falsch geschriebenen Wortes (%s) markiert." % (wrong) 
                correctmark = True

            elif choice == 'r':
                replacement = pywikibot.input('Replace "%s" with?' % wrong)
                mynewtext = text.replace(wrong, replacement)
                if mynewtext == text: 
                    return None

                pywikibot.showDiff(text, mynewtext)
                mycomment = "Tippfehler entfernt: %s -> %s" % (wrong, replacement) 

            elif choice == 'ra': 
                print "Replace all with "
                replacement = pywikibot.input('Replace "%s" with?' % wrong)
                # TODO we used to have a separate dict for this (replaceNew)
                self.pm.markReplaced(wrong, correct)
                mynewtext = text.replace(wrong, replacement)
                if mynewtext == text: 
                    return None
                pywikibot.showDiff(text, mynewtext)
                mycomment = "Tippfehler entfernt: %s -> %s" % (wrong, replacement) 

            elif choice in ['n', ']']: 
                return None

            elif choice == 'x': 
                return "x"

            else: 
                return None

