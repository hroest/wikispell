#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Script that identifies misspelled words from a SQL table that contains two columns:

    - smallword : the word itself
    - occurence : the word frequency

""" 

import MySQLdb
from wikispell.WordFrequencyChecker import WordFrequencyChecker
from wikispell.BlacklistSpellchecker import BlacklistSpellchecker
from wikispell.InteractiveWordReplacer import InteractiveSearchReplacer
from wikispell.PermanentWordlist import PermanentWordlist
## pywikibot imports
try:
    import wikipedia as pywikibot
    import pagegenerators
except ImportError:
    import pywikibot
    from pywikibot import pagegenerators

################################################################################

# Database config
MYSQL_CONFIG = "~/.my.cnf.hroest"
db_dump = "20160203";
db_dump = "wikiwords.countedwords_20160203";
WORD_MINOCC = 1000;
WORD_MINLEN = 13;

################################################################################
# Find the most common words and search for missspells of those 
################################################################################
db = MySQLdb.connect(read_default_file=MYSQL_CONFIG)
cursor = db.cursor()

cursor.execute(
"""
select * from %s where occurence > %s
and length(smallword) > %s
order by occurence DESC
"""  % (db_dump, WORD_MINOCC, WORD_MINLEN)
)
misspell = cursor.fetchall()


pm = PermanentWordlist("User:HRoestTypo", load=True)
interactive_replacer = InteractiveSearchReplacer(pm=pm)
freq_checker = WordFrequencyChecker(pm)

try:
    j = -1
    while j < len(misspell):
        j += 1
        myw = misspell[j][1]
        myw = myw.decode('utf8')
        print "================================="
        print myw, j, "out of", len(misspell)
        ## TODO: make sure you adjust these parameters:
        #   - occurence_cutoff
        #   - lcutoff
        #   - ldistance
        #   - askUser
        candidates = bb.find_candidates(myw, cursor,
                                occurence_cutoff = 25, lcutoff = 0.85, ldistance = 2,
                                db_=db_dump)
        print "nr candidates", len(candidates)

        if len(candidates) == 0: 
            continue

        pages = freq_checker.load_candidates(myw, candidates, askUser=False) 

        print "will do", len(pages), "pages"
        wrongwordlist = [p.wrong for p in pages]

        gen = pagegenerators.PreloadingGenerator(pages)
        interactive_replacer.checkit(gen, wrongwordlist, myw)
    
except KeyboardInterrupt:
    print "Keyboard interrupt, will exit gracefully"
except Exception as e:
    print "Caught unhandled exception", e
    raise e

# Finally
pm.store_wikipedia()

