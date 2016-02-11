#!/bin/sh 

# This script downloads and processes a new data dump for de-wiki
# Run as
# ./newdata TIMESTAMP

if [ -z "$1" ]
  then
    echo "No argument supplied, please use dump date as first argument (e.g. 20151029)"
    exit
fi

echo "Will proceed with $1"

# Remove old links, download current (latest) article dump
rm -f dewiki-curr.xml.bz2
wget https://dumps.wikimedia.org/dewiki/latest/dewiki-latest-pages-articles.xml.bz2 -O dewiki-$1-pages-articles.xml.bz2
ln -s dewiki-$1-pages-articles.xml.bz2 dewiki-curr.xml.bz2

# possibly cd here, esp if you dont want the data dumps at the same place 
# cd ...

python setup_mysql_in_memory.py ../data/dewiki-curr.xml.bz2 wikiwords.countedwords_${1}
python spellcheck_wordlist.py -xmlfile:../data/dewiki-curr.xml.bz2 -non-interactive \
   -batchNr:250000 -blacklist:perturbations.dic -pageStore:Benutzer:HRoestTypo/Tippfehler/$1/

