#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
This bot spellchecks Wikipedia pages using a list of known "bad" words. 
It can be used in the following ways:

spellcheck_wordlist.py Title
    Check a single page
spellcheck_wordlist.py -cat:Category
    Check all pages in the given category (recursively)
python spellcheck_wordlist.py -xmlfile:/path/to/wiki-latest-pages-articles.xml
    Check all pages in the given XML file
python spellcheck_wordlist.py -searchWiki
    Checks all pages containing the wrong word (using the websearch functionality) 

Wordlists can be provided in one of following formats (note: all words need to be in lowercase):

-typopage:         Provide a wikipage that contains one entry per line, namely a template with three parameters: article, wrong word, correct word
-blacklist:        Provide a file that contains a list of wrong words (provide the wrong and the correct word per line separated by semicolon ";")
-singleword:       To search and replace a single word use "wrongword;correctword"
-blacklistpage:    Link to a specific page where the words are listed using "*" and separated by ":"
-pageStore:        Store the result on a Wikipedia page instead of interactively asking the user

Command-line options:
-batchNr:          Size of batches for the XML file processing

A good example of a "blacklist" of words can, for example, be found at 
https://raw.githubusercontent.com/hroest/spellcheck-data/master/lists/de/perturbations.dic

Example usage:

    spellcheck_wordlist.py -searchWiki -singleword:"Dölli;test"
    spellcheck_wordlist.py Uttwil -singleword:"goldschmied;test"
    spellcheck_wordlist.py -xmlfile:/media/data/tmp/wiki/dewiki-latest-pages-articles.xml.bz2 -singleword:"und;test" -batchNr:10

    spellcheck_wordlist.py -blacklist:blacklist.dic -recentchanges

    spellcheck_wordlist.py -blacklistpage:User:HRoestTypo/replacedDerivatives -cat:Schweiz
    spellcheck_wordlist.py -blacklistpage:User:HRoestTypo/replacedDerivatives -searchWiki

    spellcheck_wordlist.py -blacklistpage:User:HRoestTypo/replaced -searchWiki

    spellcheck_wordlist.py -typopage:Benutzer:HRoestTypo/Tippfehler/20151002/63

    python spellcheck_wordlist.py -searchWiki -blacklist:concat.dic

    spellcheck_wordlist.py -xmlfile:data/dewiki-latest-pages-articles.xml.bz2 -non-interactive -batchNr:1000 \
                                -pageStore:User:HRoestTypo/Tippfehler/

"""

#
# Distributed under the terms of the MIT license.
#

import wikipedia as pywikibot
import pagegenerators, catlib
import re, string, sys

from wikispell.SpellcheckLib import Word, WrongWord
from wikispell.SpellcheckLib import readBlacklist
from wikispell.SpellcheckLib import InteractiveWordReplacer
from wikispell.SpellcheckLib import abstract_Spellchecker
import numpy

NUMBER_PAGES = 60

def doSearchWiki(wordlist, blacklistChecker, pageStore=None):

    # Simple search and replace ...
    i = 0

    correctWords_page = 'Benutzer:HRoestTypo/Tippfehler/all/correctWords'

    ignorePages_page = 'Benutzer:HRoestTypo/Tippfehler/all/ignorePages'
    wr = InteractiveWordReplacer()
    loadPagesWiki(wr, correctWords_page, ignorePages_page)

    UPDATE_EVERY = 1000

    nr_output = 0
    output = ""
    for wrong, correct in wordlist.iteritems():
        i += 1

        wrong_lower = wrong.lower()

        print "== Replace %s with %s" % (wrong, correct), "(%s out of %s)" % (i, len(wordlist))
        s = pagegenerators.SearchPageGenerator(wrong, number=NUMBER_PAGES, namespaces='0')
        gen = pagegenerators.PreloadingGenerator(s, pageNumber=NUMBER_PAGES)

        # If we have no page to store our results, we probably want an interactive search and replace 
        if pageStore is None:
            print "Simple search and reaplce ... "
            blacklistChecker.simpleReplace(gen, wrong_lower, correct)
            continue

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
            wrongwords = blacklistChecker.spellcheck_blacklist(
                text, {wrong : correct}, return_words=True, title=page.title())

            if len(wrongwords) == 0: 
                continue

            title = page.title()

            # Skip pages
            if title in wr.ignorePages: 
                continue

            # for w in page.words:
            if True:
                w = WrongWord(wrong, correctword=correct)

                # Skip specific words
                if title in wr.ignorePerPages and \
                   w.word in wr.ignorePerPages[title]: continue

                wrong = w.word
                correct = w.correctword

                if len(wrong) == 0:
                    continue
                if wrong.lower() == correct.lower():
                    continue
                
                if wrong[0].lower() != wrong[0]:
                    # upper case
                    correct = correct[0].upper() + correct[1:]

                output += "{{User:HRoestTypo/V/Typo|%s|%s|%s}}\n" %  (title, w.word, correct)
                nr_output += 1

        if i % UPDATE_EVERY == 0:
            print "put page with content:", output
            mypage = pywikibot.Page(pywikibot.getSite(), pageStore)
            mypage.put(output,  u'Update' )

def writeTyposToWikipedia(res, page_name):
    output = ""
    for r in res:
        # {{User:HRoestTypo/V/Typo|Johann Heinrich Zedler|Maerialien|Materialien}}
        page = r
        title = page.title

        # Skip pages
        if title in wr.ignorePages: 
            continue

        for w in page.words:

            # Skip specific words
            if title in wr.ignorePerPages and \
               w.word in wr.ignorePerPages[title]: continue

            wrong = w.word
            correct = w.correctword

            if len(wrong) == 0:
                continue
            if wrong.lower() == correct.lower():
                continue
            
            if wrong[0].lower() != wrong[0]:
                # upper case
                correct = correct[0].upper() + correct[1:]

            output += "{{User:HRoestTypo/V/Typo|%s|%s|%s}}\n" %  (title, w.word, correct)
            nr_output += 1

    mypage = pywikibot.Page(pywikibot.getSite(), page_name)
    mypage.put(output,  u'Update' )
    myIter += 1

def loadPagesWiki(wr, correctWords_page, ignorePages_page):
    # Load correct words
    mypage = pywikibot.Page(pywikibot.getSite(), correctWords_page)
    text = mypage.get()
    lines = text.split('* ')[1:]
    correctWords = {}
    for l in lines:
        spl =  l.split(' : ')
        tmp = correctWords.get( spl[0], [] )
        tmp.append( spl[1].strip() )
        correctWords[spl[0]] = tmp

    print "loaded %s correct words" % len(correctWords)

    # Load ignore pages
    mypage = pywikibot.Page(pywikibot.getSite(), ignorePages_page)
    text = mypage.get()
    lines = text.split('* ')[1:]
    ignorePages = []
    for l in lines:
        ignorePages.append(l.strip())

    print "loaded %s ignored pages " % len(ignorePages)

    wr.ignorePages = ignorePages
    wr.ignorePerPages = correctWords


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

def collectBlacklistPages(batchNr, gen, badDict):
    """Collect all wrong words in the provided page generator.
    """

    wrongWords = []
    seenAlready = {}

    for i, page in enumerate(gen):

        if not page.namespace() == 0: 
            continue

        if page.title() in seenAlready: 
            continue
        seenAlready[ page.title() ] = 0 # add to seen already

        # Get text
        try:
            text = page.get()
        except pywikibot.NoPage:
            pywikibot.output(u"%s doesn't exist, skip!" % page.title())
            continue
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"%s is a redirect, skip!" % page.title())
            continue

        # Process page
        page.words = BlacklistSpellchecker().spellcheck_blacklist(text, badDict, return_words=True)

        if not len(page.words) == 0: 
            wrongWords.append(page)

        if batchNr > 0 and i > batchNr: 
            break

    return wrongWords, i

def processXMLWordlist(xmlfile, badDict, batchNr = 3000, breakUntil = '',
                       doNoninteractive=False, pageStore=None):
    from SpellcheckLib import InteractiveWordReplacer
    import xmlreader

    wr = InteractiveWordReplacer()
    generator = xmlreader.XmlDump(xmlfile).parse()

    correctWords_page = 'Benutzer:HRoestTypo/Tippfehler/all/correctWords'
    ignorePages_page = 'Benutzer:HRoestTypo/Tippfehler/all/ignorePages'

    if True:
        print "Load pages with correct words and ignored pages ... "

        loadPagesWiki(wr, correctWords_page, ignorePages_page)

    def collectBlacklistPagesXML(batchNr, gen, badDict):
        """Collect all wrong words in the provided page generator.
        """
        wrongWords = []
        seenAlready = {}
        i = 0
        for page in gen:
            if not page.ns == '0':
                continue
            # Process page
            page.words = BlacklistSpellchecker().spellcheck_blacklist(page.text, badDict, return_words=True, range_level="full")
            if not len(page.words) == 0: 
                wrongWords.append(page)
            if batchNr > 0 and i >= batchNr: 
                break
            i += 1
            print i, page.title
        return wrongWords, i

    # Fast-forward until a certain page
    i = 0
    currentpage = None
    if not breakUntil == '':
        for page in generator:
            currentpage = page
            if page.title == breakUntil: 
                break
            i += 1
            if i % 100 == 0:
                sys.stdout.flush()
                sys.stdout.write("\rSearched pages: %s" % i)

    print("\nStarting to work on batches")

    if doNoninteractive:

        nrpages = batchNr
        myIter = 1
        nr_output = 0

        # Noninteractive processing: process all articles in batches (until
        # there are no more pages)
        while nrpages == batchNr:
            res, nrpages = collectBlacklistPagesXML(nrpages, generator, badDict)

            # Output page
            page_name = pageStore + str(myIter)

            writeTyposToWikipedia(res, page_name)

        print "Write number of wrong words", nr_output
        return

    # Loop:
    # - process a batch of pages
    # - work on them interactively
    while True:
        wrongWords, nrpages = collectBlacklistPagesXML(batchNr, generator, badDict)

        print('Found %s wrong words.' % len(wrongWords))
        res = []
        for p in wrongWords:
            r = pywikibot.Page(pywikibot.getSite(),p.title)
            r.words = p.words
            res.append(r)

        wr.processWrongWordsInteractively( res )

        choice = pywikibot.inputChoice('Load next batch?',
               ['Yes', 'yes', 'No', 'Save choices'], ['y', '\\', 'n', 's'])

        if choice == 'n' or choice == 's': 

            # Save correct words
            output = ""
            for k in sorted(wr.ignorePerPages):
                vlist = wr.ignorePerPages[k]
                for v in sorted(vlist):
                    output += "* %s : %s\n" % (k, v)

            mypage = pywikibot.Page(pywikibot.getSite(), correctWords_page)
            mypage.put(output,  u'Update' )

            output = ""
            for k in sorted(wr.ignorePages):
                output += "* %s \n" % (k.strip())

            # Save ignore pages
            mypage = pywikibot.Page(pywikibot.getSite(), ignorePages_page)
            mypage.put(output,  u'Update' )

        if choice == 'n': 
            break


    errors = False
    doneSaving = True
    for call in wr.Callbacks:
        try:
            if not call.error is None:
                print('could not save page %s because\n:%s' % (call.page,
                       call.error)); errors = True
        except AttributeError:
            print('not done yet with saving')
            doneSaving = False

    if not errors and doneSaving:
        print('saved all pages')

def main():
    ###################################################################
    #                           MAIN                                  #
    ###################################################################
    searchWiki = False
    recentChanges = False
    singleWord = None
    blacklistfile = None
    blacklistpage = None
    category = None
    xmlfile = None
    typopage = None
    pageStore = None
    title = []
    batchNr = 1000
    non_interactive = False

    for arg in pywikibot.handleArgs():
        if arg.startswith("-blacklist:"):
            blacklistfile = arg[11:]
        if arg.startswith("-recentchanges"):
            recentChanges = True
        elif arg.startswith("-blacklistpage:"):
            blacklistpage = arg[15:]
        elif arg.startswith("-typopage:"):
            typopage = arg[10:]
        elif arg.startswith("-singleword:"):
            singleWord = arg[12:]
        elif arg.startswith("-searchWiki"):
            searchWiki = True
        elif arg.startswith("-xmlfile:"):
            xmlfile = arg[9:]
        elif arg.startswith("-pageStore:"):
            pageStore = arg[11:]
        elif arg.startswith("-batchNr:"):
            batchNr = int(arg[9:])
        elif arg.startswith("-non-interactive"):
            non_interactive = True
        elif arg.startswith("-cat:"):
            category = arg[5:]
        elif arg.startswith('-h') or arg.startswith('--help'):
            pywikibot.showHelp()
            return
        else:
            title.append(arg)

    # This is a purely interactive bot, we therefore do not want to put-throttle
    pywikibot.put_throttle.setDelay(1)

    # Load wordlist
    #  -> this is non-exclusive, e.g. combinations of lists are possible ... 
    wordlist = {}

    if singleWord:
        spl = singleWord.split(";")
        wordlist = dict([  [spl[0].strip(), spl[1].strip()]  ])

    if blacklistfile:
        readBlacklist(blacklistfile, wordlist)

    if blacklistpage:
        mypage = pywikibot.Page(pywikibot.getSite(), blacklistpage)
        text = mypage.get()
        lines = text.split('* ')[1:]
        for l in lines:
            spl =  l.split(' : ')
            wordlist[spl[0].lower()] = spl[1].strip().lower()

    if typopage:
        mypage = pywikibot.Page(pywikibot.getSite(), typopage)
        text = mypage.get()
        pages = {}
        print "Will generate for ", len(text.splitlines()), "words"

        # Iterate through page with words to replace
        for line in text.splitlines():
            if len(line) > 4:
                inner = line.strip()[2:-2]
                elem = inner.split("|")
                title = elem[1]

                wrongWord = elem[2]
                correctWord = elem[3]

                if len(wrongWord) < 5 or len(correctWord) < 5:
                    print "skip", title, ":", wrongWord
                    continue

                if title in pages:
                    page = pages[title]
                    page.words.append( [ wrongWord, correctWord ] )
                else:
                    page = pywikibot.Page(pywikibot.getSite(), title) 
                    page.words = [ [ wrongWord, correctWord ] ]
                    pages[ title ] = page

        # Retrive text for pages to work on
        print "Will generate for ", len(pages), "pages"
        gen = pagegenerators.PreloadingGenerator(pages.values(), pageNumber=NUMBER_PAGES)

        # Iterate all pages to work on
        wr = InteractiveWordReplacer()
        for page in gen:
            print "================================"
            print page

            if page.title().startswith("Liste der Biografien"):
                print "Skip %s" % "Liste der Biografien"
                continue

            try:
                text = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist, skip!" % page.title())
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, skip!" % page.title())
                continue

            wDict = dict( [ (w[0].lower(), w[1].lower() ) for w in page.words])

            if len(wDict) == 1:
                wrong = page.words[0][0]
                occurence = text.count(wrong)

                rstr = r'\b%s\b' % (wrong)
                match = [m.group(0) for m in re.finditer(rstr, text)]
                occurence = len(match)

                # Exit if the word is common in the page
                print "Wrong word", wrong, "Occurence", occurence, " (vs %s)" % text.count(wrong)
                if occurence > 1:
                    continue

                in_enum = False
                for line in text.splitlines():
                    if line.find(wrong) != -1:

                        # Find the sentence in the line where the word was found
                        sentence = line
                        s = line.split(".")
                        for t in s:
                            if t.find(wrong) != -1:
                                sentence = t
                        
                        # Get a possible enumeration
                        enumeration = sentence.split(",")
                        if len(enumeration) < 3:
                            break

                        # Check in which part of the enumeration it is
                        found_in = -1
                        enumeration = enumeration[1:]
                        for j,e in enumerate(enumeration):
                            # print e, len(e)
                            if e.find(wrong) != -1:
                                found_in = j

                        # Check whether it is part of an enumeration
                        if found_in > 0 and found_in < len(enumeration) -1:
                            if len(enumeration[found_in-1]) < 30 and \
                               len(enumeration[found_in-0]) < 30 and \
                               len(enumeration[found_in+1]) < 30:
                                    in_enum = True
                                    print "Found in middle of enum in ", sentence
                        elif found_in + 1 == len(enumeration):
                            
                            if enumeration[found_in].find("und") != -1 and \
                               len(enumeration[found_in-1]) < 30 and \
                               len(enumeration[found_in]) < 50:
                                    in_enum = True
                                    print "Found at the end of enum ", sentence

                if in_enum:
                    continue

            # First, check whether word is present (allows early exit)
            wrongwords = BlacklistSpellchecker().spellcheck_blacklist(
                text, wDict, return_words=True, title=page.title())

            if len(wrongwords) == 0: 
                print "Skip", page.title(), "no words"
                continue

            page.words = wrongwords
            wr.processWrongWordsInteractively( [page] )

        # Print output
        for k in sorted(wr.ignorePerPages):
            vlist = wr.ignorePerPages[k]
            for v in sorted(vlist):
                print "* %s : %s" % (k, v)

        print wr.dontReplace
        return

    print "Loaded wordlist of size", len(wordlist)
    if len(wordlist) == 0:
        print "Empty wordlist, maybe you forgot something ?"
        return

    # Initiate checker
    blacklistChecker = BlacklistSpellchecker()

    if searchWiki:

        doSearchWiki(wordlist, blacklistChecker)
        return
    elif recentChanges:
            s = pagegenerators.RecentchangesPageGenerator(batchNr)
            gen = pagegenerators.PreloadingGenerator(s, pageNumber=NUMBER_PAGES)
    elif xmlfile:
        if len(title) != 0:
            title = ' '.join(title)
        else:
            title = ""

        processXMLWordlist(xmlfile, wordlist, breakUntil = title, batchNr=batchNr,
                           doNoninteractive=non_interactive,pageStore=pageStore)
        return

    elif category:
        print "using cat", category
        cat = catlib.Category(pywikibot.getSite(), category)
        gen_ = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
        gen = pagegenerators.PreloadingGenerator(gen_, pageNumber=NUMBER_PAGES)
    elif len(title) != 0:
        title = ' '.join(title)
        gen = [pywikibot.Page(pywikibot.getSite(),title)]
    else:
        print "No input articles selected. Abort."
        return

    collectFirst = True
    sp = BlacklistSpellchecker()
    sp.blackdic = wordlist
    collectedPages, nrpages = collectBlacklistPages(-1, gen, sp.blackdic)
    InteractiveWordReplacer().processWrongWordsInteractively(collectedPages)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

