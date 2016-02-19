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
    """ Interactivly replace individual words

    The main function is processWrongWordsInteractively which takes a list of
    page objects, each of which has a list of "WrongWord" objects attached to
    it. These objects describe which words need to be replaced on the page in
    question.
    """

    def __init__(self, xmldump=None):
        self.ignorePages = []
        self.ignorePerPages = {}
        self.dontReplace = []

        self.Callbacks = []

    def processWrongWordsInteractively(self, pages, offline=False):
        """This will process pages with wrong words.

        It expects a list of pages with words attached to it.
        """

        self.performReplacementList = []
        ask = True
        gen = pagegenerators.PreloadingGenerator(pages)
        for page in gen:
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
            self.dontReplace = self._checkSpellingInteractive(page, self.dontReplace)
            newtext = self._doReplacement(text, page)

            if text == newtext: 
                continue

            pywikibot.showDiff(text, newtext)
            if ask: choice = pywikibot.inputChoice('Commit?',
               ['Yes', 'yes', 'No', 'Yes to all'], ['y', '\\', 'n','a'])
            else: choice = 'y'
            #if choice == 'a': stillAsk=False; choice = 'y'
            if choice in ('y', '\\'):
                callb = CallbackObject()
                self.Callbacks.append(callb)
                page.put_async(newtext, comment=page.typocomment, callback=callb)

    def _checkSpellingInteractive(self, page, dontReplace):
        """Interactively goes through all wrong words in a page.

        All we do here is save doReplace = True if we want to replace it, while
        doReplace will do the actual replacement.
        Uses self.ignorePerPages and a local dontReplace
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
            if self.ignorePerPages.has_key(title) \
               and smallword in self.ignorePerPages[title]: 
                continue
            if smallword in dontReplace:
                if self.ignorePerPages.has_key( title ):
                    self.ignorePerPages[title].append( smallword)
                else: 
                    self.ignorePerPages[ title ] = [ smallword ]
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
                dontReplace.append(w.word) 
                if self.ignorePerPages.has_key( title ):
                    self.ignorePerPages[title].append( smallword)
                else: self.ignorePerPages[ title ] = [ smallword ]
            if choice in ('n', ']'): 
                if self.ignorePerPages.has_key( title ):
                    self.ignorePerPages[title].append( smallword)
                else: self.ignorePerPages[ title ] = [ smallword ]
                continue
            if choice == 'x': 
                self.ignorePages.append( title );
                return dontReplace
            if choice == 'r':
                w.replacement = pywikibot.input(u"What should I replace \"%s\" by?"
                                              % bigword.word)
                w.doReplace = True
            if choice in ( 'y','\\'):
                w.replacement = bigword.replace(sugg)
                w.doReplace = True

        return dontReplace

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
    """ Interactivly replace individual words using search and replace
    """

    def __init__(self, pm=None):

        self.pm = pm

    def checkit(self, pages, wrongs, g_correct, spellchecker):
        """
        Takes a list of pages and associated wrong words and goes through them
        one by one, asking user input to correct it.
        """

        for i,page in enumerate(pages):
            wrong = wrongs[i]
            correct = g_correct
            if wrong in self.pm.replaceNew:
                correct = self.pm.replaceNew[wrong]

            print "Starting work on", page.title(), "word:", wrong

            if wrong.lower() in self.pm.noall:
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

            myranges = spellchecker.forbiddenRanges(text, level="moderate")
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

            #  -> next look for the lower case version of the word
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

            if not self.pm.rcount.has_key(mywrong): 
                self.pm.rcount[mywrong] = 0

            pywikibot.showDiff(text, newtext)
            a = self._ask_user_input(page, mywrong, correct, newtext, text)
            if a is not None and a == "x":
                print "Exit, go to next"
                return

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
                self.pm.noall.update( [ wrong.lower() ] )
                return None
            elif choice in ('y', '\\'):
                if not self.pm.replace.has_key(wrong) and not correctmark:
                    self.pm.replace[wrong] = correct
                if not correctmark: 
                    self.pm.rcount[wrong] += 1
                # TODO : return rather than put
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
                self.pm.replaceNew[ wrong ]  = replacement
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


