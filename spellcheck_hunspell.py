#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
This bot spellchecks Wikipedia pages using the hunspell spellcheck engine.  It
can be used in four ways:

spellcheck_hunspell.py Title
    Check a single page; after this the bot will ask whether you want to
    check another page
spellcheck._hunspellpy -start:Title
    Go through the wiki, starting at title 'Title'.
spellcheck_hunspell.py -newpages
    Go through the pages on [[Special:Newpages]]
spellcheck_hunspell.py -longpages
    Go through the pages on [[Special:Longpages]]

For each unknown word, you get a couple of options:
    numbered options: replace by known alternatives
    a: This word is correct; add it to the list of known words
    c: The uncapitalized form of this word is correct; add it
    i: Do not edit this word, but do also not add it to the list
    p: Do not edit this word, and consider it correct for this page only
    r: Replace the word, and add the replacement as a known alternative
    s: Replace the word, but do not add the replacement
    *: Edit the page using the gui
    g: Give a list of 'guessed' words, which are similar to the given one
    x: Ignore this word, and do not check the rest of the page

Command-line options:
-html          change HTML-entities like &uuml; into their respective letters.
               This is done both before and after the normal check.
-dictionary:   Location of the hunspell dictionary (-dictionary:/usr/share/hunspell/de_DE).
-common_words: Location of a file with common words

Example usage (you can find the dictionaries on https://github.com/hroest/spellcheck-data):

python spellcheck_hunspell.py  -dictionary:/usr/share/hunspell/de_DE -common_words:spellcheck-data/lists/de/common_15.dic  -language:DE  Schweiz

"""

"""
To install hunspell, you need to install the libhunspell as well as pyhunspell:
sudo apt-get install libhunspell-dev
wget http://pyhunspell.googlecode.com/files/hunspell-0.1.tar.gz
tar xzvf hunspell-0.1.tar.gz; cd hunspell-0.1/
sudo python setup.py install

# then you need to install the dictionaries in your language:
sudo apt-get install hunspell-de-de-frami
sudo apt-get install hunspell-de-ch-frami

"""
#
# Distributed under the terms of the MIT license.
#

import re, sys
import string, codecs
import hunspell, webbrowser
import pickle
import time

# Importing pywikibot
try:
    import wikipedia as pywikibot
    import pagegenerators
    import xmlreader
    from catlib import Category
    newBot = False
except ImportError:
    import pywikibot
    from pywikibot import pagegenerators
    from pywikibot import xmlreader
    from pywikibot.page import Category
    newBot = True

from wikispell.Callback import CallbackObject
from wikispell.SpellcheckLib import askAlternative
from wikispell.InteractiveWordReplacer import InteractiveWordReplacer
from wikispell.HunspellSpellchecker import HunspellSpellchecker

def run_bot(allPages, sp, pageStore=None, level="full"):
    Callbacks = []
    stillSkip  = False;
    firstPage = True
    nonInteractive = True

    wr = InteractiveWordReplacer()
    # loadPagesWiki(wr, correctWords_page, ignorePages_page)
    output = ""

    if pageStore is None:
        nonInteractive = False

    UPDATE_EVERY = 10000
    # UPDATE_EVERY = 100
    update_nr = 1

    page_nr = 0
    for page in allPages:

        try:
            if not page.ns == '0': continue
            text = page.get()
            page_title = page.title
        except AttributeError:
            page_title = page.title()

        print "Performing spellcheck on page %s (%s pages processed so far)" % (page_title.encode("utf8"), page_nr)
        page_nr += 1

        st = time.time()
        try:
            text = page.get()
        except pywikibot.NoPage:
            pywikibot.output(u"%s doesn't exist, skip!" % page_title)
            continue
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"%s is a redirect, skip!" % page_title)
            continue

        # print "get pg time: ", time.time() - st

        st = time.time()
        orig_text = text

        text, wrongWords = sp.spellcheck(text, level=level)

        if not nonInteractive:
            text = sp.askUser(text, page_title)
        else:
            # print "got wrong words here", len(wrongWords)

            if page_nr % UPDATE_EVERY == 0:
                # print "put output", output
                curr_page = pageStore + str(update_nr)
                mypage = pywikibot.Page(pywikibot.getSite(), curr_page)
                mypage.put(output,  u'Update' )
                update_nr += 1
                output = ""

            # skip pages without wrong words ...
            if len(wrongWords) == 0:
                sp.clearCache()
                continue

            for w in wrongWords:

                # Skip specific words
                if page_title in wr.ignorePerPages and \
                   w.word in wr.ignorePerPages[page_title]: continue

                wrong = w.word
                wrong = w.derive()
                correct = ""
                correct = w.correctword

                if len(wrong) == 0:
                    continue
                if wrong.lower() == correct.lower():
                    continue

                if wrong[0].lower() != wrong[0] and len(correct) > 0:
                    # upper case
                    correct = correct[0].upper() + correct[1:]

                output += "{{User:HRoestTypo/V/Typo|%s|%s|%s}}\n" % (page_title, w.derive(), correct)

        sp.clearCache()

        # print "analysis time: ", time.time() - st

        if text == orig_text:
            continue

        pywikibot.output('\03{lightred}===========\nDifferences to commit:\n\03{default}');
        pywikibot.showDiff(orig_text, text)

        choice = pywikibot.inputChoice('Commit?', ['Yes', 'No'], ['y', 'n'])
        if choice == 'y':
            comment = "Fix typographical error"
            callb = CallbackObject()
            Callbacks.append(callb)
            page.put_async(text, comment=comment, callback=callb)

    for k, v in sp.knownwords.iteritems():
        print "* %s : %s" % (k,v)

def main():
    ###################################################################
    #                           MAIN                                  #
    ###################################################################
    title = []
    start = None
    newpages = False
    longpages = False
    rebuild = False
    category = None
    checklang = None
    dictionary = None
    common_words = None
    nosuggestions = False
    remove_dissimilar = True
    pageStore = None
    correct_html_codes = False
    xmlfile = False
    language = "DE"
    level="full"
    stringent = 0
    composite_minlen = 0
    for arg in pywikibot.handleArgs():
        if arg.startswith("-start:"):
            start = arg[7:]
        elif arg.startswith("-stringent:"):
            stringent = int(arg[11:])
        elif arg.startswith("-xmlfile:"):
            xmlfile = arg[9:]
        elif arg.startswith("-cat:"):
            category = arg[5:]
        elif arg.startswith("-keepDissimilar"):
            remove_dissimilar = False
        elif arg.startswith("-excludeText:"):
            level = arg[13:]
        elif arg.startswith("-dictionary:"):
            dictionary = arg[12:]
        elif arg.startswith("-newpages"):
            newpages = True
        elif arg.startswith("-common_words:"):
            common_words = arg[14:]
        elif arg.startswith("-longpages"):
            longpages = True
        elif arg.startswith("-minlen:"):
            composite_minlen = int(arg[8:])
            print "minlen", composite_minlen
        elif arg.startswith("-nosugg"):
            nosuggestions = True
        elif arg.startswith("-language"):
            language = arg[10:]
        elif arg.startswith("-html"):
            correct_html_codes = True
        elif arg.startswith("-pageStore:"):
            pageStore = arg[11:]
        elif arg.startswith('-h') or arg.startswith('--help'):
            pywikibot.showHelp()
            return
        else:
            title.append(arg)
            print "title", arg

    if language not in ["DE", "EN"]:
        print "Language needs to be either DE or EN"
        return

    common_words_dict = set([])

    if True:
        if common_words is not None:
            for wordfile in common_words.split(";"):
                if len(wordfile) == 0:
                    continue
                f = open(wordfile)
                for l in f:
                    common_words_dict.add(l.strip().decode("utf8").lower())

        print "Got %s known good words from the supplied file" % len(common_words_dict)

    sp = HunspellSpellchecker(hunspell_dict = dictionary,
                              minimal_word_size=4,
                              nosuggestions = nosuggestions,
                              language = language,
                              stringent = stringent
                              composite_minlen = composite_minlen,
                              remove_dissimilar=remove_dissimilar,
                              common_words=common_words_dict)
    sp.correct_html_codes = correct_html_codes
    sp.nosuggestions = nosuggestions

    if start and not category:
        gen = pagegenerators.PreloadingGenerator(
            pagegenerators.AllpagesPageGenerator(start=start,includeredirects=False))
    elif category:
        site = pywikibot.getSite()
        cat = Category(site, category)

        myStart = None
        if start:
            myStart = start

        # Going through categories was easier with the old bot...
        if not newBot:
            cgen = pagegenerators.CategorizedPageGenerator(cat, start=myStart)
            gen = pagegenerators.PreloadingGenerator(cgen)
        else:
            if not myStart:
                cgen = pagegenerators.CategorizedPageGenerator(cat)
            else:
                # When we want to continue where we left off, we have to select the starting point ourselves:
                articles = sorted(pagegenerators.CategorizedPageGenerator(cat), key = lambda x: x.title()  )
                cgen = []
                skip = True
                for p in articles:
                    if p.title() == myStart:
                        skip = False
                    if not skip:
                        cgen.append( p )

            # Preload the pages
            gen = pagegenerators.PreloadingGenerator(cgen, usePageIds=False)
    elif xmlfile:
        gen = xmlreader.XmlDump(xmlfile).parse()
    elif newpages:
        def wrapper_gen():
            for (page, length) in pywikibot.getSite().newpages(500):
                yield page
        gen = wrapper_gen()
    elif longpages:
        def wrapper_gen():
            for (page, length) in pywikibot.getSite().longpages(500):
                yield page
        gen = wrapper_gen()
    elif len(title) != 0:
        title = ' '.join(title)
        gen = [pywikibot.Page(pywikibot.getSite(),title)]
    else:
        ####################################
        #Examples
        site = pywikibot.getSite()
        cat = Category(site,'Kategorie:Staat in Europa')
        cat = Category(site,'Kategorie:Schweizer')
        cgen = pagegenerators.CategorizedPageGenerator(cat)
        gen = pagegenerators.PreloadingGenerator(cgen)

    run_bot(gen, sp, pageStore=pageStore, level=level)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

