#!/usr/bin/python
# -*- coding: utf-8  -*-
"""

Script to read an xml dump of Wikipedia and write it to an SQL table 

find the dumps here: 

https://dumps.wikimedia.org/dewiki/latest/

Run this script with 2 arguments
- location of the xml dump (dewiki-latest-pages-articles.xml.bz2)
- mysql table to create

This script will simply create a single table with all words, which then needs
to processed further. Note that this can be disk-space intensive.
""" 
#
# Distributed under the terms of the MIT license.
#

import MySQLdb
import spellcheck
import wikipedia as pywikibot
import pagegenerators
import BlacklistChecker
import sys
import xmlreader
from spellcheck_wordlist import BlacklistSpellchecker

MYSQL_CONFIG = "~/.my.cnf.hroest"
db_dump = sys.argv[1]
xml_dump = sys.argv[2]

print "Working with database ", db_dump
print "Working with file ", xml_dump

cursor.execute( """create table %s (
    article_id int,
    smallword varchar(255)
) ENGINE = MYISAM; """ % db_dump)

db = MySQLdb.connect(read_default_file=MYSQL_CONFIG)
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
    table = "insert into %s" % db_dump 
    tmp = cursor.executemany( table + " (article_id, smallword) values (%s,%s)", prepare )
    db.commit()

"""
Next, execute these commands:

drop table hroest.countedwords_%(dump)s;
create table countedwords_%(dump)s as
select count(*)  as occurrence, smallword as word from
all_words_%(dump)s group by smallword;
alter table hroest.countedwords_%(dump)s add index(occurrence);
alter table hroest.countedwords_%(dump)s add index(word);

""" 

