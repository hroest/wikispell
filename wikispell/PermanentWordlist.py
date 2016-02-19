#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
A class used for permanent storage of wordlists

"""

import re

## pywikibot imports
try:
    import wikipedia as pywikibot
    import pagegenerators
except ImportError:
    import pywikibot
    from pywikibot import pagegenerators


class PermanentWordlist():

    def __init__(self, prefix, load=True):

        # A dictionary of {wrong : correct}
        self.replace = {}
        # A list of words that are correct
        self.noall = set([])
        # A count of which wrong words were replaced how often
        self.rcount = {}

        # A list of words that are correct on a certain page {title : correct}
        self.correctPerPage = {}

        self.replaceNew = {}

        self.prefix = prefix 

        if load:
            self.load_wikipedia()

    def checkIsIgnored(self, title, wrong, correct=None):
        if title is not None:
            if title in self.correctPerPage and wrong in self.correctPerPage[title]:
                return True

        if wrong in self.noall:
            return True

        return False

    def markReplaced(self, wrong, correct):
        self.replace[wrong] = correct

        # update count 
        tmp = self.rcount.get(wrong, 0)
        self.rcount[wrong] = tmp + 1

    def markCorrectWord(self, correct):
        assert not isinstance(correct, list)
        self.noall.update( [correct] )

    def markCorrectWords(self, correct):
        assert isinstance(correct, list)
        self.noall.update(correct)

    def markCorrectWordPerPage(self, page, correct):
        tmp = self.correctPerPage.get( page, [])
        tmp.append(correct)
        self.correctPerPage[page] = tmp

    #
    ## Load and store dictionary data from Wikipedia
    # 
    def load_wikipedia(self):

        mypage = pywikibot.Page(pywikibot.getSite(), '%s/replaced' % self.prefix)
        text = mypage.get()
        lines = text.split('* ')[1:]
        self.replace = {}
        for l in lines:
            spl =  l.split(' : ')
            if len(spl) != 2:
               continue
            self.replace[spl[0]] = spl[1].strip()

        mypage = pywikibot.Page(pywikibot.getSite(), '%s/correctPerPage' % self.prefix)
        text = mypage.get()
        lines = text.split('* ')[1:]
        self.correctPerPage = {}
        for l in lines:
            spl = l.split(' : ')
            if len(spl) != 2:
               continue

            # append to list of correct words on that page
            tmp = self.correctPerPage.get( spl[0], [] )
            newWord = spl[1].strip() 
            if newWord not in tmp:
                tmp.append(newWord)
            self.correctPerPage[spl[0]] = tmp

        mypage = pywikibot.Page(pywikibot.getSite(), '%s/correct' % self.prefix)
        text = mypage.get()
        lines = text.split('* ')[1:]
        self.noall = set([])
        for l in lines:
            self.noall.update( [ l.strip() ] )

        mypage = pywikibot.Page(pywikibot.getSite(), '%s/replacCount' % self.prefix)
        text = mypage.get()
        lines = text.split('* ')[1:]
        self.rcount = {}
        for l in lines:
            spl =  l.split(':')
            if len(spl) != 2:
               continue
            self.rcount[spl[0].strip()] = int(spl[1].strip() )

    def store_wikipedia(self):

        s = ''
        for k in sorted(self.replace.keys()):
            s += '* %s : %s\n' % (k, self.replace[k])
        mypage = pywikibot.Page(pywikibot.getSite(), '%s/replaced' % self.prefix)
        mypage.put_async( s )

        s = ''
        for k in sorted(self.correctPerPage.keys()):
            vlist = self.correctPerPage[k]
            for v in sorted(vlist):
                s += '* %s : %s\n' % (k, v)
        mypage = pywikibot.Page(pywikibot.getSite(), '%s/correctPerPage' % self.prefix)
        mypage.put_async( s )

        s = ''
        for k in sorted(self.noall):
            s += '* %s \n' % (k)
        mypage = pywikibot.Page(pywikibot.getSite(), '%s/correct' % self.prefix)
        mypage.put_async( s )

        s = ''
        for k in sorted(self.rcount.keys()):
            if self.rcount[k] > 0: s += '* %s : %s\n' % (k, self.rcount[k])
        mypage = pywikibot.Page(pywikibot.getSite(), '%s/replacCount' % self.prefix)
        mypage.put_async( s )
        s = ''

