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

