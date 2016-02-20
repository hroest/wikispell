#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
Uses a set of rules to exclude words to analyze
"""
#
# Distributed under the terms of the MIT license.
#

import re, sys
import string, codecs
import time

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

        #
        #  () - if it contains a number
        #
        if any(char.isdigit() for char in smallword) or \
           any(char in [")", "("] for char in smallword):
            return True

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
                                                           u"í", u"ø"] for char in smallword):
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
                return True
            if smallword.startswith("re") and smallword[2:] in self.common_words:
                return True
            if smallword.endswith("ization") and smallword[:-7] in self.common_words:
                return True
            if smallword.endswith("ly") and smallword[:-2] in self.common_words:
                return True
            if smallword.endswith("ee") and smallword[:-2] in self.common_words:
                return True

        if self.language == "DE":
            if smallword.startswith("un") and smallword[2:] in self.common_words:
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

