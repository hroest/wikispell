#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
A library of spellchecking helper classes and functions
"""
#
# Distributed under the terms of the MIT license.
#

import time, sys
import re, string
import codecs

# local imports
from Word import Word, WrongWord
from AbstractSpellchecker import abstract_Spellchecker

## pywikibot imports
try:
    import wikipedia as pywikibot
    import pagegenerators
except ImportError:
    import pywikibot
    from pywikibot import pagegenerators

class SpecialTerm(object):
    def __init__(self, text):
        self.style = text

edit = SpecialTerm("edit")
endpage = SpecialTerm("end page")

def askAlternative(bigword, knownwords = {}, newwords = [], context=None, title='', replaceBy=None,correct_html_codes=False):
    word = bigword.derive()
    correct = None
    pywikibot.output(u"=" * 60)
    pywikibot.output(u"Found unknown word '%s' in '%s'" % (word, title))
    if context:
        pywikibot.output(u"Context:")
        pywikibot.output(u"" + context)
        pywikibot.output(u"-" * 60)
    while not correct:
        w_alternatives = bigword.getAlternatives()
        for i in xrange(len(w_alternatives)):
            pywikibot.output(u"%s: Replace by '%s'"
                             % (i+1,
                                w_alternatives[i]))
        pywikibot.output(u"a: Add '%s' as correct"%word)
        if word[0].isupper():
            pywikibot.output(u"c: Add '%s' as correct" % (uncap(word)))
        pywikibot.output(u"i: Ignore once (default)")
        pywikibot.output(u"p: Ignore on this page")
        pywikibot.output(u"r: Replace text")
        pywikibot.output(u"s: Replace text, but do not save as alternative")
        pywikibot.output(u"g: Guess (give me a list of similar words)")
        pywikibot.output(u"*: Edit by hand")
        pywikibot.output(u"x: Do not check the rest of this page")
        answer = pywikibot.input(u":")
        if answer == "":
            answer = "i"
        if answer in "aAiIpP":
            correct = word
            if answer in "aA":
                knownwords[word] = word
                newwords.append(word)
            elif answer in "pP":
                pageskip.append(word)
        elif answer in "rRsS":
            correct = pywikibot.input(u"What should I replace it by?")
            if answer in "rR":
                if correct_html_codes:
                    correct = removeHTML(correct)
                if correct != cap(word) and \
                   correct != uncap(word) and \
                   correct != word:
                    try:
                        knownwords[word] += [correct.replace(' ', '_')]
                    except KeyError:
                        knownwords[word] = [correct.replace(' ', '_')]
                    newwords.append(word)
                knownwords[correct] = correct
                if not replaceBy is None: replaceBy[word] = correct
                newwords.append(correct)
        elif answer in "cC" and word[0].isupper():
            correct = word
            knownwords[uncap(word)] = uncap(word)
            newwords.append(uncap(word))
        elif answer in "gG":
            possible = getalternatives(word)
            if possible:
                print "Found alternatives:"
                for pos in possible:
                    pywikibot.output("  %s" % pos)
            else:
                print "No similar words found."
        elif answer == "*":
            correct = edit
        elif answer == "x":
            correct = endpage
        else:
            for i in xrange(len(w_alternatives)):
                if answer == str(i + 1):
                    correct = w_alternatives[i]
                    if not replaceBy is None: replaceBy[word] = correct
    return correct

def uncap(string):
    # uncapitalize the first word of the string
    if len(string) > 1:
        return string[0].lower() + string[1:]
    else:
        return string.lower()


def cap(string):
    # uncapitalize the first word of the string
    return string[0].upper() + string[1:]

def readBlacklist(filename, badDict, encoding="utf8"):
    """
    Read in a list of wrong words
    """
    f = codecs.open(filename, 'r', encoding = encoding)
    for line in f.readlines():
        # remove trailing newlines and carriage returns
        try:
            while line[-1] in ['\n', '\r']:
                line = line[:-1]
        except IndexError:
            pass
        #skip empty lines
        if line != '':
            line = line.split(';')
            badDict[ line[0].lower() ] = line[1]

def writeBlacklist(filename, encoding, badDict):
    """
    Write out a list of wrong words
    """
    f = codecs.open(filename, 'w', encoding = encoding)
    for key in sorted(badDict.keys()):
        f.write('%s;%s\n' % (key, badDict[key]))
    f.close()

if __name__ == "__main__":
    pass
