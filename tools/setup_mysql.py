#!/usr/bin/python
# -*- coding: utf-8  -*-
"""

Script to read an xml dump of Wikipedia and write it to an SQL table 

find the dumps here: 

https://dumps.wikimedia.org/dewiki/latest/

Run this script with 2 arguments
- location of the xml dump (dewiki-latest-pages-articles.xml.bz2)
- mysql table to create

This script will simply create a single table with all words, which then needs to processed further.
""" 

import MySQLdb
import spellcheck
import wikipedia as pywikibot
import pagegenerators
import BlacklistChecker
import sys
import xmlreader
from spellcheck_wordlist import BlacklistSpellchecker

db_dump = sys.argv[1]
xml_dump = sys.argv[2]

print "Working with database ", db_dump
print "Working with file ", xml_dump

db = MySQLdb.connect(read_default_file="~/.my.cnf.hroest")
db.autocommit(True)
cursor = db.cursor()
sp = BlacklistSpellchecker()
wikidump = xmlreader.XmlDump(xml_dump)
gen = wikidump.parse()
for i, page in enumerate(gen):
    if not page.ns == '0': 
        continue

    if i % 100 == 0:
        print i, page.title

    prepare = [ [page.id, p.encode('utf8')] for p in sp.spellcheck_blacklist(page.text, {}, return_for_db=True)]
    table = "insert into hroest.all_words_%s" % db_dump 
    tmp = cursor.executemany( table + " (article_id, smallword) values (%s,%s)", prepare )
    db.commit()

# cursor.execute( "select count(*) from hroest.all_words_20151002" )

"""
drop table hroest.countedwords_%(dump)s ;
create table countedwords_%(dump)s as
select count(*)  as occurence, smallword as word from
all_words_%(dump)s group by smallword;
alter table hroest.countedwords_%(dump)s add index(occurence);
alter table hroest.countedwords_%(dump)s add index(word);
""" 

