#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
Uses a set of rules to exclude words to analyze

This is mostly used by the hunspell spellchecker as it produces many false positives.
"""
#
# Distributed under the terms of the MIT license.
#

import re, sys
import string, codecs
import time

class RuleBasedWordAnalyzer():

    def __init__(self, minimal_word_size, multiple_occurrence_tol, language,
                 stringent, common_words, common_words_filter = None, composite_minlen = 0):

        self.minimal_word_size = minimal_word_size
        self.multiple_occurrence_tol = multiple_occurrence_tol
        self.language = language
        self.common_words = common_words
        self.composite_minlen = composite_minlen
        self.stringent = stringent

        self.common_words_filter = common_words_filter
        if self.common_words_filter is None:
            self.common_words_filter = {}


    def skipWord(self, smallword, text, loc, use_alt):
        
        #  If hunspell doesn't know it, doesn't mean it is not correct
        #  This not only reduces the number of words considered to be
        #  incorrect but also makes it much faster since the feature
        #  hunspell.suggest takes most time (~6x speedup).

        # A few print functions, use as "pr(sm)"
        sm = smallword
        def pr(sm):
            return sm.encode("utf8")

        #
        #  (a) - if it contains a number
        #
        if any(char.isdigit() for char in smallword) or \
           any(char in [")", "("] for char in smallword):
            return True

        #
        #  (b) - we check whether it is following an internal link like [[th]]is
        #
        if loc > 2 and text[loc-2:loc] == ']]':
            return True

        if self.stringent > 1000:
            return False

        #  (c) - Remove common words and words that are derivative of the
        #        common word (plural in english, genetiv in german)
        #
        if smallword.lower() in self.common_words_filter:
            return True

        if smallword.lower() in self.common_words:
            return True

        if self.language in ["DE", "EN"] and \
          len(smallword) > 3 and \
          smallword[-1:] == 's' and  \
          (smallword[:-1].lower() in self.common_words or
           smallword[:-1].lower() in self.common_words_filter ):
            return True
        
        #
        #  (d) - we check whether it is less than n characters long
        #
        if len(smallword) < self.minimal_word_size:
            return True

        if self.stringent > 500:
            return False

        #
        #  (e) - skip if the word occurs more than n times in the text
        #
        if text.count(smallword) > self.multiple_occurrence_tol:
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
                
                # If the first part is a known good word, check whether we have
                # a composite word
                if first_part in self.common_words:

                    other_part = smallword[i:].lower()

                    # A few rules for English
                    if self.language == "EN":
                        if other_part in ["ly"]:
                            # print "Skip English composite word ending with ly: ", pr(sm)
                            return True
                        elif other_part in self.common_words:
                            # print "Skip English composite word", pr(sm[0:i]), pr(sm[i:])
                            return True

                    # Rest of the rules are for German

                    # Simple heuristic for german word combinations using "keit"
                    elif len(first_part) > 4 and other_part in ["keit"]:
                        # print "Skip: German combination", pr(sm[0:i]), "+", pr(sm[i:])
                        return True

                    # We should not trust suffixes that are less than 3
                    # characters long, but some of them are true declensions in
                    # German. Note we still require the stem (root word) to be
                    # of length 4 or more. These suffixes are listed
                    # explicitely and allowed here:
                    #
                    #  - n/r/s/e/en/er/es/em mostly for adjectives
                    #  - en, e, s, ei for nouns
                    #
                    #
                    #  - see https://de.wikipedia.org/wiki/Deutsche_Deklination#Grunds.C3.A4tze 
                    #  - see https://de.wikipedia.org/wiki/Deutsche_Deklination#Starke_Deklination_der_Adjektive
                    elif len(other_part) < 3 and len(first_part) > 3:

                        if smallword[0].islower() and other_part in ["n", "r", "s", "e",
                                "en", "er", "es", "em"]:
                            # print "is lower: ", smallword[0].islower()
                            # print "Skip: German declension", pr(sm[0:i]), "+", pr(sm[i:])
                            return True

                        elif smallword[0].isupper() and other_part in ["en", "ei", "e", "s"]:
                            # print "Skip: upper ", smallword[0].isupper()
                            # print "Skip: German declension", pr(sm[0:i]), "+", pr(sm[i:])
                            return True

                        elif other_part in self.common_words:
                            # print "SPECIAL: strange ending!!!: ", pr(sm[0:i]), "+", pr(sm[i:])
                            pass


                    elif self.language == "DE" and other_part in ["ern"]:
                        # print "SPECIAL: strange ending ern !!!: "
                        pass

                    elif len(other_part) <= self.composite_minlen:
                        continue

                    elif other_part in self.common_words:
                        #  should have fugen-s
                        #  - bei Zusammensetzungen mit Wörtern auf -tum, -ling, -ion, -tät, -heit, -keit, -schaft, -sicht, -ung 
                        if self.language == "DE" and \
                          (len(first_part) > 3 and first_part[-3:] in ["tum", "ion", u"tät", "ung"] or \
                          first_part.endswith("ling") or \
                          first_part.endswith("heit") or \
                          first_part.endswith("keit") or \
                          first_part.endswith("schaft") or \
                          first_part.endswith("sicht") ):
                            # Probably needs a fugen-s, we should now allow it 
                            # print "donot skip: missing fugen-s", kkk(sm[0:i]), kkk(sm[i:])
                            pass
                        else:
                            ### print self.language == "DE" and len(first_part) > 3
                            ### print first_part[-3:] in ["tum", "ion", u"tät", "ung"] 
                            ### print "skip: composite word", kk[0:i], kk[i:]

                            ### 
                            ### # print first_part[-3:]
                            ### print first_part[-3:] in ["tum", "ion", u"tät", "ung"]
                            ### print first_part.encode("utf8")[-3:] in ["tum", "ion", u"tät", "ung"]

                            # print "skip: composite word", kkk(sm[0:i]), kkk(sm[i:])
                            return True

                    elif i +2 < len(smallword) and smallword[i:i+1] == "s" and len(first_part) > 2:
                        # potential "Fugenlaut" in German, see https://de.wikipedia.org/wiki/Fugenlaut
                        other_part = smallword[i+1:].lower()

                        # Exclude some cases where it should not occur
                        # http://www.spiegel.de/kultur/zwiebelfisch/zwiebelfisch-der-gebrauch-des-fugen-s-im-ueberblick-a-293195.html
                        if first_part[-2:] in ["er", "el", "en", "ss", u"ß", "st", "tz"] or \
                           first_part.endswith("sch") or \
                           first_part.endswith("s") or \
                           first_part.endswith("z"):
                            pass
                            # print "donot skip: should not have fugen-s", kkk(sm[0:i]), kkk(sm[i:])
                        elif other_part in self.common_words:
                            # print "skip: composite fugenlaut", kkk(sm[0:i]), "+s+", kkk(sm[i+1:])
                            return True

                    # try composite word in German with 1-letter ending
                    elif self.language == "DE" and \
                            other_part[:len(other_part)-1] in self.common_words and \
                            len(first_part) > 2 and \
                            len(other_part) > 4 + 1 and \
                            other_part[len(other_part)-1:] in ["n", "r", "s", "e"]:
                        # print "SPECIAL: skip composite word (1 letter)", smallword[0:i].encode("utf8"), "+", smallword[i:].encode("utf8")
                        return True

                    # try composite word in German with 2-letter ending
                    elif self.language == "DE" and \
                            other_part[:len(other_part)-2] in self.common_words and \
                            len(first_part) > 2 and \
                            len(other_part) > 4 + 2 and \
                            other_part[len(other_part)-2:] in ["en", "er",  "es", "em"]:
                        # print "SPECIAL: skip composite word (2 letter)", smallword[0:i].encode("utf8"), "+", smallword[i:].encode("utf8")
                        return True

                    other_part = smallword[i:].lower()

        return False

