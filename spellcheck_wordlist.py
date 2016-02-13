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

import re, string, sys

## pywikibot imports
try:
    import wikipedia as pywikibot
    import pagegenerators
    from catlib import Category
except ImportError:
    import pywikibot
    from pywikibot import pagegenerators
    from pywikibot.page import Category

from wikispell.SpellcheckLib import Word, WrongWord
from wikispell.SpellcheckLib import readBlacklist
from wikispell.SpellcheckLib import InteractiveWordReplacer
from wikispell.SpellcheckLib import abstract_Spellchecker
from wikispell.BlacklistSpellchecker import BlacklistSpellchecker
import numpy

NUMBER_PAGES = 60
NUMBER_PAGES = 50

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

        try:
            s = pagegenerators.RecentchangesPageGenerator(number=batchNr)
        except TypeError:
            # new pywikibot
            s = pagegenerators.RecentchangesPageGenerator(total=batchNr, namespaces=[0], 
                    showRedirects=False, _filter_unique=pywikibot.tools.filter_unique)

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
        cat = Category(pywikibot.getSite(), category)
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

