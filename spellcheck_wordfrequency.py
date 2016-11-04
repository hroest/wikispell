#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Script that identifies misspelled words from a SQL table that contains two
columns (this table may be generated from an XML dump using the script
setup_mysql_in_memory.py) :

    - smallword : the word itself
    - occurence : the word frequency

This script then iterate through the most common words and tries to identify
similar words that occur with very low frequency and are thus likely
misspellings of the more common word. The low frequency words are then searched
in Wikipedia and replaced with the correct word.

Potential usage:

    python spellcheck_wordfrequency.py --db wikiwords.countedwords_20161020

"""

import MySQLdb
from wikispell.WordFrequencyChecker import WordFrequencyChecker
from wikispell.BlacklistSpellchecker import BlacklistSpellchecker
from wikispell.InteractiveWordReplacer import InteractiveSearchReplacer
from wikispell.PermanentWordlist import PermanentWordlist

try:
    import wikipedia as pywikibot
    import pagegenerators
except ImportError:
    import pywikibot
    from pywikibot import pagegenerators

################################################################################

# Database config
##MYSQL_CONFIG = "~/.my.cnf.hroest"
## db_dump = "20160203";
## db_dump = "wikiwords.countedwords_20160203";
## WORD_MINOCC = 1000;
## WORD_MINLEN = 13;


import argparse, sys

parser = argparse.ArgumentParser()
parser.add_argument('--db', dest="db", required=True, help="database table (e.g. wikiwords.countedwords_20160203)")
parser.add_argument('--lower_cutoff', dest="lower_cutoff", default=13, type=int, help="Word minimum length")
parser.add_argument('--upper_cutoff', dest="upper_cutoff", default=999, type=int, help="Word maximum length")
parser.add_argument('--occurrence_cutoff', dest="occurrence_cutoff", default=1000, type=int, help="Occurrence cutoff, script will only consider words that occur at least this often in the database.")
parser.add_argument('--skip_words', dest="skip_words", default=0, type=int, help="Skip first N words")
parser.add_argument('--pageStore', dest="pageStore", default="", help="Wikipedia page to store results of script (making it non-interactive)")
parser.add_argument('--mysql_config', dest="mysql_config", default="~/.my.cnf.hroest", help="MySQL config file")

# Advanced arguments to fine-tune which words will be asked
parser.add_argument('--candidate_cutoff', dest="candidate_cutoff", default=25, type=int, help="Consider words occurring more often than this cutoff as correct.")
parser.add_argument('--min_lratio', dest="min_lratio", default=0.85, type=float, help="Only consider words with at least this minimal Levenshtein ratio")
parser.add_argument('--max_ldistance', dest="max_ldistance", default=3, type=int, help="Only consider words with less than this maximal Levenshtein distance")
parser.add_argument('--askUserForWord', action='store_true', default=False, help="Ask user for each word which variations to consider (can be turned on in interactive mode)")

args = parser.parse_args(sys.argv[1:])

doInteractive = True
if len(args.pageStore) > 0:
    doInteractive = False
    # pageStore = args.pageStore + "%s_max_%s" % (args.db, args.lower_cutoff)
    pageStore = args.pageStore

# Database config
## MYSQL_CONFIG = "~/.my.cnf.hroest"
## db_dump = "20160203";
## db_dump = "wikiwords.countedwords_20160203";
## WORD_MINOCC = 1000;
## WORD_MINLEN = 13;

################################################################################
# Find the most common words and search for misspellings of those
################################################################################
db = MySQLdb.connect(read_default_file=args.mysql_config)
cursor = db.cursor()

cursor.execute(
"""
select * from %s where occurence > %s
and length(smallword) > %s
and length(smallword) <= %s
order by occurence DESC
"""  % (args.db, args.occurrence_cutoff, args.lower_cutoff, args.upper_cutoff)
)
misspell = cursor.fetchall()


pm = PermanentWordlist("User:HRoestTypo", load=True)
interactive_replacer = InteractiveSearchReplacer(pm=pm)
freq_checker = WordFrequencyChecker(pm)

#UPDATE_EVERY = 250
UPDATE_EVERY = 50
update_nr = 1
output = ""
try:
    j = -1
    while j < len(misspell)-1:
        j += 1

        if j < args.skip_words:
            continue

        if not doInteractive and j % UPDATE_EVERY == 0:
            print "put output", output
            curr_page = pageStore + str(update_nr)
            mypage = pywikibot.Page(pywikibot.getSite(), curr_page)
            mypage.put(output,  u'Update' )
            update_nr += 1
            output = ""


        myw = misspell[j][1]
        myw = myw.decode('utf8')
        print "================================="
        print myw, j, "out of", len(misspell)

        candidates = freq_checker.find_candidates(myw, cursor,
                                occurence_cutoff = args.candidate_cutoff,
                                lcutoff = args.min_lratio,
                                ldistance = args.max_ldistance,
                                db_=args.db)

        print "nr candidates", len(candidates)
        if len(candidates) == 0:
            continue

        pages = freq_checker.load_candidates(myw, candidates, askUser=args.askUserForWord)

        print "will do", len(pages), "pages"
        wrongwordlist = [p.wrong for p in pages]

        gen = pagegenerators.PreloadingGenerator(pages)
        output += interactive_replacer.checkit(gen, wrongwordlist, myw, interactive=doInteractive)

except KeyboardInterrupt:
    print "Keyboard interrupt, will exit gracefully"
except Exception as e:
    print "Caught unhandled exception", e
    raise e

# Finally
if doInteractive:
    pm.store_wikipedia()
if not doInteractive:
    print "put output", output
    curr_page = pageStore + str(update_nr)
    mypage = pywikibot.Page(pywikibot.getSite(), curr_page)
    mypage.put(output,  u'Update' )
    update_nr += 1
    output = ""

