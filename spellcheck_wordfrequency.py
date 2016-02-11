#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Script that identifies misspelled words from a SQL table that contains two columns:

    - smallword : the word itself
    - occurence : the word frequency

""" 
import MySQLdb

import pagegenerators
import wikipedia as pywikibot

from wikispell.BlacklistSpellchecker import BlacklistSpellchecker
from wikispell.BlacklistChecker import BlacklistChecker

################################################################################

# Database config
MYSQL_CONFIG = "~/.my.cnf.hroest"
db_dump = "20160203";

################################################################################
# Find the most common words and search for missspells of those 
################################################################################
db = MySQLdb.connect(read_default_file=MYSQL_CONFIG)
cursor = db.cursor()

cursor.execute(
"""
select * from wikiwords.countedwords_%s where occurence > 1000
and length(smallword) > 13
order by occurence DESC
"""  % db_dump)
misspell = cursor.fetchall()

bb = BlacklistChecker.Blacklistchecker()
sp = BlacklistSpellchecker()

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
                                db_='wikiwords.countedwords_%s' % db_dump)
        print "nr candidates", len(candidates)

        if len(candidates) == 0: 
            continue

        pages = bb.load_candidates(myw, candidates, askUser=False) 

        print "will do", len(pages), "pages"
        wrongwordlist = [p.wrong for p in pages]
        gen = pagegenerators.PreloadingGenerator(pages)
        bb.checkit(gen, wrongwordlist, myw, sp)
    
except KeyboardInterrupt:
    bb.store_wikipedia()
    print "Keyboard interrupt, will exit gracefully"
except Exception as e:
    bb.store_wikipedia()
    print "Caught unhandled exception", e
    raise e

bb.store_wikipedia()

