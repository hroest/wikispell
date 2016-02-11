
import pagegenerators
import MySQLdb
import wikipedia as pywikibot
import BlacklistChecker as temp
from spellcheck_wordlist import BlacklistSpellchecker
import BlacklistChecker
################################################################################
# db = MySQLdb.connect(read_default_file="~/.my.cnf.hroest", charset = "utf8", use_unicode = True)
db = MySQLdb.connect(read_default_file="~/.my.cnf.hroest")
cursor = db.cursor()

sp = BlacklistSpellchecker()
# db_dump = "20151002_n";
db_dump = "20160111";
db_dump = "20160203";

# Top 10k words:
# +-----------+---------------------------+
# |      3190 | Kunde                     |
# +-----------+---------------------------+
# 10000 rows in set (0.02 sec)

################################################################################
# Find the most common words and search for missspells of those 
# {{{
################################################################################

cursor.execute(
"""
select * from wikiwords.countedwords_%s where occurence > 1000
and length(smallword) > 13
order by occurence DESC
"""  % db_dump)
misspell = cursor.fetchall()

import BlacklistChecker
bb = BlacklistChecker.Blacklistchecker()

try:
    j = -1
    #for j in range(700):
    while j < len(misspell):
        j += 1
        if j < 1000: continue
        # if j < 2717: continue
        myw = misspell[j][1]
        myw = myw.decode('utf8')
        print "================================="
        print myw, j, "out of", len(misspell)
        candidates = bb.find_candidates(myw, cursor,
                                occurence_cutoff = 25, lcutoff = 0.85, ldistance = 2,
                                db_='wikiwords.countedwords_%s' % db_dump)
        print "nr candidates", len(candidates)
        if len(candidates) == 0: continue
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

# }}}
