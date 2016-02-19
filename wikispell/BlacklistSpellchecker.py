#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
A class for performing a spellcheck using a word list
"""

#
# Distributed under the terms of the MIT license.
#

import time, sys
import re, string
from SpellcheckLib import abstract_Spellchecker
from InteractiveWordReplacer import InteractiveWordReplacer
from Word import Word, WrongWord

class BlacklistSpellchecker(abstract_Spellchecker):
    """ Blacklist based spellchecker

    This spellchecker reads in a "blacklist" of words that are commonly spelled
    wrong and checks a gien text against this list.

    Possible usage
    >>> sp = BlacklistSpellchecker()
    >>> result = sp.spellcheck_blacklist(text, {'Deuschland' : 'wrong'})
    """

    def __init__(self):
        self.rcount = {}

    def spellcheck_blacklist(self, text, badDict, return_for_db=False,
                             return_words=False, title=None, verbose=False,
                             range_level="moderate"):
        """ Checks a single text against the words in the blacklist and returns
        a list of wrong words.
        """

        loc = 0 # the current location in the text we parse
        old_loc = 0
        curr_r = 0
        ranges = self.forbiddenRanges(text, level=range_level)

        ranges = sorted(ranges)
        wrongWords = []
        prepare = []
        j = 0

        while True:
            #added "/" to first since sometimes // is in the text
            #added "/" to second since in german some words are compositions
            wordsearch = re.compile(r'([\s\=\<\>\_/-]*)([^\s\=\<\>\_/\-]+)')
            #wordsearch = re.compile(r'([\s\=\<\>\_]*)([^\s\=\<\>\_/\-]+)') #old one
            if verbose:
                print "== Start wordsearch at location", loc
            match = wordsearch.search(text,loc)
            LocAdd = 0
            j = j + 1

            if not match:
                # No more words on this page
                break

            if verbose:
                print j, "Check '%s'" % text[ match.start():match.end()], "at loc", loc

            # Check if we are in forbidden range
            curr_r, loc, in_nontext = self.check_in_ranges(ranges, 
                                       match.start(), match.end(), curr_r, loc)

            if verbose:
                print "    -> moved loc pointer to ", loc, "skip is", in_nontext

            if in_nontext:
                continue

            # Split the words up at special places like &nbsp; or a dash
            spl = re.split('&nbsp;', match.group(2))
            if len(spl) > 1: 
                LocAdd = 5
            elif len(spl) == 1:
                spl = re.split(u'–', spl[0])

            loc_start = loc + len(match.group(1)) # start of the word
            ww = spl[0]
            LocAdd += len(ww) + 1
            bigword = Word(ww)
            smallword = bigword.derive()

            if verbose:
                print "    ==> smallword", smallword

            done = False
            for r in ranges:
                # If the end of the range coincides with the start of the word
                # we might not have a full word -> rather discard it.
                if r[1] == loc_start:
                    loc += LocAdd
                    done = True

            if done:
                continue

            # We advance the location by the characters skipped (group 1)
            loc += len(match.group(1))
            done = self._text_skip(text, loc, smallword, title)
            if verbose:
                print "    new loc (after accounting for skipped chars)", loc, "which is '%s'" % match.group(1)

            ###################################
            #use this code to insert into the database
            if return_for_db:
                if not done:
                    wrongWords.append(smallword)

            else:
                ###################################
                #here we check whether it is wrong
                if not done and smallword.lower() in badDict \
                   and not smallword == '' and not smallword.isupper():

                    if not smallword == badDict[smallword.lower()]:
                        if return_words:
                            wrongWords.append(
                                WrongWord(wrong_word = smallword,
                                          location = loc, 
                                          bigword = bigword.word,
                                          correctword = badDict[smallword.lower()]
                                ) 
                            )
                        else:
                            wrongWords.append([smallword, bigword, loc, badDict[smallword.lower()],
                                text[max(0, loc-100):min(loc+100, len(text))] ])

            # We advance the location by the characters of the word (group 2)
            loc += LocAdd
            if verbose:
                print "    new loc (after accounting for word)", loc, "we are at", text[loc]

        return wrongWords

    def _text_skip(self, text, loc, word, title=None):

        #exclude words that are smaller than 3 letters
        if len( word.lower() ) < 3: 
            return True

        # if we have ''' before, we dont want to interpret
        if loc > 3 and text[loc-3:loc] == "'''" or \
            text[loc:loc+3] == "'''" :
            return True

        # if we have a <nowiki></nowiki> break before, we dont want to interpret
        if loc > 17 and text[loc-17:loc] == '<nowiki></nowiki>':
            return True

        # if we have a closing wikilink "]]" before, we dont want to interpret
        if loc > 2 and text[loc-2:loc] == ']]':
            return True

        # try to find out whether its an abbreviation and has a '.' without capitalization
        if loc+len(word)+5 < len(text) and \
           text[loc+len(word)] == '.' and \
           text[loc+len(word)+2].islower() and \
           not text[loc+len(word):loc+len(word)+5] == '<ref>':
            return True

        # words that end with ' or -
        if loc+len(word) < len(text) and text[loc+len(word)] == '-':
            return True

        # words that start with " -"
        if loc > 1 and text[loc-1] == "-" and text[loc-2] == " ":
            return True

        #exclude words that have uppercase letters in the middle
        for l in word[1:]:
            if l.isupper(): 
                return True

        # Get possible genetiv, derive word stem and search whether the word
        # occurs somewhere in the text
        if word[0].isupper() and word[-1] == "s":
            stem = word[:-1]
            try:
                rstr = r'\b%s\b' % (word[:-1])
                match_stem =  [m.group(0) for m in re.finditer(rstr, text)]
                if len(match_stem) > 1:
                    return True
            except Exception:
                pass

        # Check whether the name exists in the title
        if title is not None:
            for title_word in title.split():
                if title_word == word:
                    return True
                if word.find(title_word) != -1:
                    return True
                if title_word.find(word) != -1:
                    return True

        return False

    def spellcheck_blacklist_regex(self, text, badDict, return_for_db=False, return_words=False):

        ranges = self.forbiddenRanges(text)
        ranges = sorted(ranges)

        wrongWords = []
        for word, replacement in badDict.iteritems():
            word_re = re.compile(word, re.IGNORECASE)
            allOccurences = [m.start() for m in re.finditer(word_re, text)]
            wordDiff = len(word) - len(replacement)
            currDiff = 0
            for loc in allOccurences:

                # Words that are parts of other words should be ignored
                if not text[loc-1] in string.whitespace:
                    continue

                if self._text_skip(text, loc, text[loc:loc+len(word)]):
                    continue

                done = False
                for r in ranges:
                    if loc > r[0] and loc < r[1]:
                        done = True
                        break

                if not done:
                    wrongWords.append([word, Word(word), loc, badDict[word.lower()],
                      text[max(0, loc-100):min(loc+100, len(text))] ])

        return wrongWords

    def simpleReplace(self, gen, wrong, correct, verbose=True):
        """ Replaces the word by a simple string operation
        wrong word and go through them one by one.
        """

        # Ensure that empty words do not trigger an exception
        if len(wrong) == 0 or len(correct) == 0: 
            return

        for page in gen:

            try:
                text = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist, skip!" % page.title())
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, skip!" % page.title())
                continue

            # First, check whether word is present (allows early exit)
            wrongwords = self.spellcheck_blacklist(text, {wrong : correct}, return_words=True, title=page.title())
            if len(wrongwords) == 0: 
                continue

            page.words = wrongwords

            InteractiveWordReplacer().processWrongWordsInteractively( [page] )

