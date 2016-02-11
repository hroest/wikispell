#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
A class for storing a wrong word identified during spellcheck
"""

#
# Distributed under the terms of the MIT license.
#

import time, sys
import re, string
import wikipedia as pywikibot

class Word(object):

    def __init__(self, text):
        self.word = text
        self.suggestions = None

    def __str__(self):
        return self.word

    def __len__(self):
        return len(self.word)

    def __cmp__(self,other):
        return self.word.__cmp__(str(other))

    def derive(self):
        # Get the short form of the word, without punctuation, square
        # brackets etcetera
        shortword = self.word
        # Remove all words of the form [[something:something - these are
        # usually interwiki links or category links
        if shortword.rfind(':') != -1:
            if -1 < shortword.rfind('[[') < shortword.rfind(':'):
                shortword = ""
        # Remove barred links
        if shortword.rfind('|') != -1:
            if -1 < shortword.rfind('[[') < shortword.rfind('|'):
                shortword = shortword[:shortword.rfind('[[')] + shortword[
                    shortword.rfind('|') + 1:]
            else:
                shortword = shortword[shortword.rfind('|') + 1:]
        shortword = shortword.replace('[', '')
        shortword = shortword.replace(']', '')
        #replace all occurencs of &nbsp;
        shortword = shortword.replace('&nbsp;', ' ')
        shortword = shortword.replace('nbsp;', ' ')
        # Remove non-alphanumerical characters at the start
        try:
            while shortword[0] in string.punctuation + u'«»–−→“„‚‘’':
                shortword = shortword[1:]
        except IndexError:
            return ""
        # Remove non-alphanumerical characters at the end; no need for the
        # try here because if things go wrong here, they should have gone
        # wrong before
        while shortword[-1] in string.punctuation + u'«»–−→“„‚‘’':
            shortword = shortword[:-1]
        # Do not check URLs
        if shortword.startswith("http://") or shortword.startswith("https://") or shortword.startswith("www."):
            shortword=""
        # Do not check 'words' with only numerical characters
        number = True
        for i in xrange(len(shortword)):
            if not (shortword[i] in string.punctuation or
                    shortword[i] in string.digits):
                number = False
        if number:
            shortword = ""
        return shortword

    def replace(self, rep):
        """Replace the short form by 'rep'. Keeping simple for now - if the
        short form is part of the long form, replace it. If it is not, ask the
        user

        """
        if rep == self.derive():
            return self.word
        if self.derive() not in self.word:
            return pywikibot.input(
                u"Please give the result of replacing %s by %s in %s:"
                % (self.derive(), rep, self.word))
        return self.word.replace(self.derive(), rep)

    def isCorrect(self, checkalternative=False):
        """If checkalternative is True, the word will only be found incorrect
        if it is on the spelling list as a spelling error. Otherwise it will be
        found incorrect if it is not on the list as a correctly spelled word.

        """
        if self.word == "":
            return True
        if self.word in pageskip:
            return True
        try:
            if knownwords[self.word] == self.word:
                return True
            else:
                return False
        except KeyError:
            pass
        if self.word != uncap(self.word):
            return Word(uncap(self.word)).isCorrect(
                checkalternative=checkalternative)
        else:
            if checkalternative:
                if checklang == 'nl' and self.word.endswith("'s"):
                    # often these are incorrect (English-style) possessives
                    return False
                if self.word != cap(self.word):
                    if Word(cap(self.word)).isCorrect():
                        return False
                    else:
                        return True
                else:
                    return True
            else:
                return False

    def getAlternatives(self):
        if not self.suggestions is None: return self.suggestions
        alts = []
        if self.word[0].islower():
            if Word(cap(self.word)).isCorrect():
                alts = [cap(self.word)]
        try:
            alts += knownwords[self.word]
        except KeyError:
            pass
        if self.word[0].isupper():
            try:
                alts += [cap(w) for w in knownwords[uncap(self.word)]]
            except KeyError:
                pass
        return [a.replace('_',' ') for a in alts]

    def declare_correct(self):
        knownwords[self.word] = self.word

    def declare_alternative(self, alt):
        if not alt in knownwords[self.word]:
            knownwords[self.word].append(word)
            newwords.append(self.word)
        return self.alternatives

class WrongWord(Word):

    def __init__(self, wrong_word, location=-1, bigword='', correctword='',
                doReplace=False):
        self.location = location
        self.bigword = bigword
        self.correctword = correctword
        self.doReplace = doReplace

        Word.__init__(self, wrong_word)

