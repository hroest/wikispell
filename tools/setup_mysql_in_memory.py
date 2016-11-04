#!/usr/bin/python
# -*- coding: utf-8  -*-
"""

Script to read an xml dump of Wikipedia and write it to an SQL table 

find the dumps here: 

https://dumps.wikimedia.org/dewiki/latest/

Run this script with 2 arguments
- location of the xml dump (dewiki-latest-pages-articles.xml.bz2)
- mysql table to create

This script will keep all words in memory and write them to a table after
processing a whole XML dump.  Note that this can be memory intensive.
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

from wikispell.BlacklistSpellchecker import BlacklistSpellchecker

MYSQL_CONFIG = "~/.my.cnf.hroest"
xml_dump = sys.argv[1]
table = sys.argv[2]

print "Working with file", xml_dump
print "Working with table", table

sp = BlacklistSpellchecker()
wikidump = xmlreader.XmlDump(xml_dump)
gen = wikidump.parse()

res = {}
for i, page in enumerate(gen):
    if not page.ns == '0': 
        continue

    if i % 100 == 0:
        print i, page.title, "unique words", len(res)

    prepare = [ [page.id, p.encode('utf8')] for p in sp.spellcheck_blacklist(page.text, {}, return_for_db=True)]
    for p in prepare:
        tmp = res.get( p[1], 0)
        res[ p[1] ] = tmp+1

db = MySQLdb.connect(read_default_file=MYSQL_CONFIG)
db.autocommit(True)
cursor = db.cursor()

cursor.execute( """create table %s (
    occurrence int,
    smallword varchar(255)
) ENGINE = MYISAM; """ % table)

insert_table = "insert into %s" % table
for k,v in res.iteritems():
    tmp = cursor.execute( insert_table + " (occurrence, smallword) values (%s,%s)", (v,k) )


cursor.execute( """alter table %s add index(occurrence) """ % table)
cursor.execute( """alter table %s add index(smallword) """ % table)

