import Levenshtein
# Python Levenshtein (apt-get install python-levenshtein) or 
# http://pypi.python.org/pypi/python-Levenshtein/
import MySQLdb
import spellcheck_hunspell as spellcheck
import wikipedia as pywikibot
import pagegenerators
import BlacklistChecker as temp
import BlacklistChecker
################################################################################
# h_lib.assert_user_can_edit( u'Benutzer:HRoestTypo/BotTestPage', u'HRoestTypo')
sp = spellcheck.Spellchecker()
sp.readBlacklist(sp.blacklistfile, sp.blacklistencoding, sp.blackdic)
sp.readIgnoreFile(sp.ignorefile, 'utf8', sp.ignorePages)
db = MySQLdb.connect(read_default_file="~/.my.cnf.hroest", charset = "utf8", use_unicode = True)
db = MySQLdb.connect(read_default_file="~/.my.cnf.hroest")
cursor = db.cursor()

bb = temp.Blacklistchecker()
db_dump = 20110514;

################################################################################
# Simple run 
################################################################################
# {{{
import BlacklistChecker
bb = BlacklistChecker.Blacklistchecker(load=True)

for i,key in enumerate(sorted(bb.replace.keys())):
    if i < 475: continue
    wrong = key
    correct = bb.replace[key]
    print "==================================="
    print "Do replace: %s with %s" % (wrong, correct)
    bb.searchNreplace(wrong, correct )

bb.store_wikipedia()

import operator
most_likely = reversed(sorted(bb.rcount.iteritems(), key=operator.itemgetter(1)))
for key, nr in most_likely:
    wrong = key
    correct = bb.replace[key]
    bb.searchNreplace(wrong, correct )

#}}}

################################################################################
# Create MySQL tables 
# {{{
################################################################################

"""
drop table hroest.all_words_%s ;
create table all_words_%s (
    article_id int,
    smallword varchar(255)
)
""" % (db_dump, db_dump)

#reload( spellcheck )
db = MySQLdb.connect(read_default_file="~/.my.cnf.hroest")
cursor = db.cursor()
sp = spellcheck.Spellchecker(xmldump = 'xmldump/extend/dewiki-latest-pages-articles.xml.bz2')
gen = sp.de_wikidump.parse()
for page in gen:
    if not page.namespace == '0': 
        continue
    prepare = [ [page.id, p.encode('utf8')] for p in sp.spellcheck_blacklist(page.text, {}, return_for_db=True)]
    table = "insert into hroest.all_words_%s" % db_dump 
    tmp = cursor.executemany( table + "(article_id, smallword) values (%s,%s)", prepare )

"""
drop table hroest.countedwords_%(dump)s ;
create table countedwords_%(dump)s as
select count(*)  as occurence, smallword as word from
all_words_%(dump)s group by smallword;
alter table hroest.countedwords_%(dump)s add index(occurence);
alter table hroest.countedwords_%(dump)s add index(word);
""" % {'dump' : db_dump }

"""
Query OK, 4788821 rows affected (16 hours 53 min 27.68 sec)
Records: 4788821  Duplicates: 0  Warnings: 0
"""

"""
create table wp_words (
    id mediumint unsigned primary key auto_increment, #up to 16777215
    word varchar(255) 
);
create table wp_articles_words (
    word_id mediumint unsigned,  #up to 16777215
    article_id mediumint unsigned
);
create table wp_countedwords (
    occurence mediumint unsigned,
    word_id mediumint unsigned
);

INSERT INTO wp_words (word) (
    SELECT DISTINCT smallword FROM hroest.all_words_%(dump)s 
);
ALTER TABLE wp_words ADD UNIQUE INDEX(word);
INSERT INTO wp_articles_words (word_id, article_id) (
    SELECT id, article_id FROM wp_words 
    INNER JOIN hroest.all_words_%(dump)s aw ON aw.smallword = wp_words.word
);
ALTER TABLE wp_articles_words ADD INDEX(word_id);
ALTER TABLE wp_articles_words ADD INDEX(article_id);
INSERT INTO wp_countedwords (occurence, word_id) (
    SELECT count(*) AS occurence, word_id FROM wp_articles_words
    group by word_id
);
ALTER TABLE wp_countedwords ADD INDEX(word_id);
ALTER TABLE wp_countedwords ADD INDEX(occurence);
""" % ('dump' : db_dump }

Query OK, 4788821 rows affected (6 hours 48 min 34.72 sec)
Query OK, 4788821 rows affected (8 min 45.82 sec)
#
Query OK, 389717523 rows affected (9 hours 11 min 22.43 sec)


# }}}

################################################################################
# Run
################################################################################
################################################################################
# here we check
# HERE WE START
###########################################################################
################################################################################
# Search and replace (single words or all possible) 
# {{{
################################################################################
wrongs = 'Universs'
corrects = 'Univers'

cursor.execute( """
select * from hroest.countedwords where word like '%s' order by occurence DESC;
""" % (wrongs+'%') )
allwrong = cursor.fetchall()

for wrong in allwrong:
    wrong = wrong[1]
    correct = wrong.replace( wrongs, corrects)
    if correct == wrong: 
        correct = wrong.replace( wrongs[1:], corrects[1:])
    print wrong, correct
    wrong = wrong.decode('utf8')
    correct = correct.decode('utf8')
    # Do a single search and replace operation using mediawiki-search
    bb.searchNreplace(wrong, correct)

#A single search and replace
wrong =   u'Dikographie'
correct =u'Diskographie'

# }}}

################################################################################
# Search and replace previously found words 
# {{{
################################################################################
# errors: [[Lady Bird Johnson]] Familiy.jpg
# [[Ehe]] - [[Datei:Brauysegen im Bett.gif|miniatur|Wye reymont vnd melusina zuamen<!--sic!-->]]

skip = True
for k in bb.replace:
    print k
    if k == u'bereit gestellt': skip = False
    if skip or k == u'bereit gestellt': continue
    wrong = k
    correct = replace[k]
    bb.searchNreplace(wrong, correct )


todo = {}
skip = True
for k in bb.replace:
    #print k
    if k == u'Bennenung': skip = False
    if skip or k == u'Bennenung': continue
    wrong = k
    correct = bb.replace[k]
    todo[wrong] = correct
    #bb.searchNreplace(wrong, correct )



import temp
reload(temp)
bb = temp.Blacklistchecker()
todo = {}
for k,v in bb.rcount.iteritems():
    if v > 5 and not k == 'bereit gestellt': 
        todo[k] = v
        print k,bb.replace[k], v


for k in sorted( todo.keys() ):
        print k,v
        v = todo[k]
        wrong = k
        correct = bb.replace[k]
        try: wrong = wrong.decode('utf8')
        except Exception: pass
        if correct.find(wrong) != -1: continue
        s = list(pagegenerators.SearchPageGenerator(wrong, namespaces='0'))
        print len(s)
        if len(list(s)) == 100:
            s = list(pagegenerators.SearchPageGenerator("%s" % wrong, namespaces='0'))
            print "now we have ", len(s), " found"
            if len(list(s)) == 100: s = s[:15]
        pages = []
        for p in s: p.wrong = wrong; pages.append(p)
        wr = [p.wrong for p in pages]
        gen = pagegenerators.PreloadingGenerator(pages)
        bb.checkit(gen, wr, correct, sp)


bb.store_wikipedia()

# }}}

################################################################################
# Find the most common words and search for missspells of those 
# {{{
################################################################################

cursor.execute(
"""
select * from hroest.countedwords_%s where occurence > 1000
and length(word) > 6
order by occurence  DESC
"""  % db_dump)
misspell = cursor.fetchall()

start finding position... Person (Grammatik)
start finding position... Insomnium
start finding position... Orbis sensualium pictus (Abbildungen)
"Liste der Abgeordneten zum Österreichischen Abgeordnetenhaus (XI. Legislaturperiode)"
Liste der Ritter des Ordens vom Heiligen Geist

# I got up to 71 : myw = misspell[71][1]

#reload(temp)
#bb = temp.Blacklistchecker()
myw = misspell[76][1]
myw = myw.decode('utf8')
print myw
candidates = bb.find_candidates(myw, cursor,
                        occurence_cutoff = 20, lcutoff = 0.8,
                        db='hroest.countedwords_%s' % db_dump)
# pages = bb.load_candidates(myw, candidates,
#                         db='hroest.countedwords_%s' % db_dump)
pages = bb.load_candidates(myw, candidates) #, db='hroest.countedwords_%s' % db_dump)

# TODO with umlaut, the "noall" doesnt work => unternehmen / unternaehme
wrongwordlist = [p.wrong for p in pages]
gen = pagegenerators.PreloadingGenerator(pages)
#bb.store_wikipedia()
# reload(temp)
# bb = temp.Blacklistchecker()
bb.checkit(gen, wrongwordlist, myw, sp)

bb.store_wikipedia()

allws = [r for r in replace if replace[r] == myw ]
corrects = myw
for wrongs in allws:
    bb.searchDerivatives(wrongs, corrects, cursor, wrongs)

# }}}

################################################################################
# use the (personal) blacklist created from permutations 
# {{{
################################################################################
cursor.execute('select * from hroest.blacklist_found')
a = cursor.fetchall()

ww = sp.spellcheck_blacklist( page.text, sp.blackdic)
self.prepare = []
for w in ww:
    self.prepare.append([page.title.encode('utf8'), page.id , w[2],
                    w[1].word, w[0], w[3], version])

cursor.executemany(
"INSERT INTO hroest.blacklist_found (%s)" % values +  
    "VALUES (%s,%s,%s,%s,%s,%s,%s)", self.prepare)

# }}}

######################################
#SPELLCHECK BLACKLIST / XML 
######################################
#http://de.wikipedia.org/w/index.php?title=Volksentscheid&diff=61305581&oldid=61265643
import spellcheck_hunspell as spellcheck
# h_lib.assert_user_can_edit( u'Benutzer:HRoestTypo/BotTestPage', u'HRoestTypo')
spellcheck.workonBlackXML(breakUntil='', batchNr=10000)

###################################
# Blacklist from the db 
# {{{
###################################

# TODO exclude everything after Literatur
# if and only if it is the latest header
# TODO exclude if line starts with *
sp.doNextBlackBatch_db(10000000, gen, db, '20101013') 

# about 50% result in 
donealready = 900
version = 20101013
pages = sp.get_blacklist_fromdb(db, donealready, version, 100)
next_done = max([p.dbid for p in pages])
sp.processWrongWordsInteractively( pages )


self.doReplace = []
self.dontReplace = []
ask = True
import pagegenerators
gen = pagegenerators.PreloadingGenerator(wrongWords)
self.total = 0
self.acc = 0
self.changed_pages = 0

wr = [p.wrong for p in pages]
bb.checkit(pages, wrongs, correct, spellchecker):




limit = 100
cursor = db.cursor()
values = """article_title, article_id, location, bigword_wrong,
        word_wrong, word_correct, version_used, id """
q = """ select %s from hroest.blacklist_found 
               where word_correct like '%s'
               and version_used = %s
               order by id limit %s
               """ % (values, 'Univers%', version, limit) 
cursor.execute(q)
lines = cursor.fetchall()
pages = sp._get_blacklist_fromdb(lines)

sp.processWrongWordsInteractively( pages )


# }}}
