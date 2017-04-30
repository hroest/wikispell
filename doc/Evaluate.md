
You can use the testfiles in tests/data/check500.tar.gz and
tests/data/check250.tar.gz to evaluate the spellchecker. Unpack them to a
directory and store their paths in a file, then run the hunspell checker:

    tar xzvf tests/data/check500.tar.gz 
    tar xzvf tests/data/check250.tar.gz 
    mv check500/ /tmp/
    mv check250/ /tmp/
    ls /tmp/check500/* > /tmp/filepaths
    ls /tmp/check250/* >> /tmp/filepaths

You can then run the spellchecker using different common words

    $ python spellcheck_hunspell.py -dictionary:/usr/share/hunspell/de_DE_frami_nhr \
        -common_words:../spellcheck-data/lists/de/common_15.dic
        -textfiles:/tmp/filepaths 

The following will evaluate 

    cat tests/data/wrong_words.txt | sort > /tmp/wrong
    grep '*99' $1 | cut -f 2 -d ' ' | sort > /tmp/found
    cat /tmp/found | uniq | wc
    wc /tmp/wrong 
    echo "False negatives:" `comm -32 /tmp/wrong /tmp/found | wc -l `
    echo "False positives:" `comm -31 /tmp/wrong /tmp/found | wc -l `

One of the main challenges remains the low precision which means many correct
words will be marked as incorrect. If you run the hunspell checker with the
regular settings (de_DE_frami) and no other wordlist, then it will report the
following

    time python spellcheck_hunspell.py -dictionary:/usr/share/hunspell/de_DE_frami -stringent:1001 -minlen:0 -nosugg -keepDissimilar -noCheckTwice -textfiles:/tmp/filepaths > results/hsp_ml0_str1001_keepDS_noTw_defaultHS
    bash doc/evaluate.sh results/hsp_ml0_str1001_keepDS_noTw_defaultHS
    Precision : .37919826652221018400
    Recall : 100.00000000000000000000
    F : .75553157042633567152

At the cost of lower recall, we can increase the F1 score from around 2% 


# use all dicts, stringent 49, use nhr5
## 174  / 18 == 174 total / 24 TP
# F = 22.2 % 
#  precision ~ 13.8%


# use all dicts, stringent 29, use nhr_new
## 139  / 23 == 139 total / 19 TP
# F = 20.99 % 
#  precision ~ 13.7 %

####################################################
# Try to increase the number of TP by having some loss in precision
# It seems the best result > 25 TP can be achieved with using comm15

# use all dicts, stringent 59, use nhr_new, comm15, minl4
## 588  / 6 == 588 total / 36 TP
# F = 11.4 % 
#  precision ~ 6.1%

# use all dicts, stringent 51, use nhr_new, comm15, ml3
## 280  / 13 == 280 total / 29 TP
# F = 18.0 % 
#  precision ~ 11.9%

# use all dicts, stringent 59, use nhr_new, comm15, minl3
## 416  / 10 == 416 total / 32 TP
# F = 13.9 % 
#  precision ~ 7.7%

####################################################
# try to use different common dicts (occuring twice), maximizing precision and F1 score:
## maximal F1 score = 27.03 % 
## maximal precision = 21.9 % 

# use all dicts, stringent 29, use nhr_new, comm2, new engtitles, noCC
## 69  / 27 == 69 total / 15 TP
# F = 27.03 % 
#  precision ~ 21.7 %

# use all dicts, stringent 29, use nhr_new, comm2
## 64  / 28 == 64 total / 14 TP
# F = 26.4 % 
#  precision ~ 21.9 %

# use all dicts, stringent 59, use nhr_new, comm2, noCC, no titles 
## 80  / 27 == 80 total / 15 TP
# F = 24.6 % 
#  precision ~ 18.75 %

# use all dicts, stringent 29, use nhr_new, comm5
## 103  / 23 == 103 total / 19 TP
# F = 26.2 % 
#  precision ~ 18.4 %

# use all dicts, stringent 29, use nhr_new, comm5 after fix (aeea0d1)
## 105  / 22 == 105 total / 20 TP
# F = 27.2 % 
#  precision ~ 19.0 %

# use all dicts, stringent 29, use nhr_new, comm10
## 127  / 23 == 127 total / 19 TP
# F = 22.5 % 
#  precision ~ 14.9 %

# use all dicts, stringent 29, use nhr_new, comm10, after fix (aeea0d1)
## 129  / 22 == 129 total / 20 TP
# F = 23.4 % 
#  precision ~ 15.5 %

# use all dicts, stringent 29, use nhr_new, comm15
## 139  / 23 == 139 total / 19 TP
# F = 20.99 % 
#  precision ~ 13.7 %


####################################################
# try to use different common paired with minlen dicts
## max F: 23%
## max Pr: 17%

# use all dicts, stringent 49, use nhr_new, comm15
## 186  / 18 == 186 total / 24 TP
# F = 21.1 % 
#  precision ~ 12.9%

# use all dicts, stringent 49, use nhr_new, comm10
## 163  / 22 == 163 total / 20 TP
# F = 19.5 % 
#  precision ~ 12.2%

# use all dicts, stringent 49, use nhr_new, comm5
## 128  / 22 == 128 total / 20 TP
# F = 23.5 % 
#  precision ~ 15.6%


# use all dicts, stringent 29, use nhr_new, comm5, minl4
## 260  / 19 == 260 total / 23 TP
# F = 15.23 % 
#  precision ~ 8.8 %

# use all dicts, stringent 29, use nhr_new, comm5, minl3
## 152  / 22 == 150 total / 20 TP
# F = 20.8 % 
#  precision ~ 13.3 %

# use all dicts, stringent 29, use nhr_new, comm2, minl3
## 87  / 27 == 87 total / 15 TP
# F = 23.3 % 
#  precision ~ 17.2 %


###########################################################################
## combine wordlists with different strigency!
## max F: 25%
## max Pr: 16.4%

bash code/combine_wordlists.sh # in spellcheck-data


# use all dicts, stringent 51, use nhr_new, comm_merge
## 134  / 20 == 134 total / 22 TP
# F = 25.0 % 
#  precision ~ 16.4%

# use all dicts, stringent 49, use nhr_new, comm_merge
## 130  / 22 == 130 total / 20 TP
# F = 23.2 % 
#  precision ~ 15.4%

# use all dicts, stringent 49, use nhr_new, comm_merge (after ddc740f25838b03)
## 132  / 22 == 132 total / 20 TP
# F = 22.9 % 
#  precision ~ 15.2%

# use all dicts, stringent 49, use nhr_new, comm_merge_str (after ddc740f25838b03)
## 155  / 19 == 155 total / 23 TP
# F = 23.3 % 
#  precision ~ 14.8%

# use all dicts, stringent 71, use nhr_new, comm_merge
## 183  / 20 == 183 total / 22 TP
# F = 19.55 % 
#  precision ~ 12.0%



# with CC dict, turn on filterdict + common words!!
## 221 / 18 == 221 total / 24 TP
# F = 18.25
# precision = 10.9

# now!
## 174 / 16 == 174 total / 26 TP
# F = 24.07 %
# precision = 14.9


# str 29
## 90 / 24 == 90 total / 18 TP
# F = 27.3 %
# precision = 20%





### get rid of redirects
# 23 FN
x Äbtissingen
x aktuelleste
x akzeptziert
x Andang
x angetriebendes
Benfiz          # Ben + fiz
Freitagstainings
x Gerichtsassesors
x Getraude
Klassikation   # skip: composite word Klassi kation : Kation [chem] + Ciulfina klassi 
Legierungem    ## SPECIAL: skip composite word (2 letter) Legie + rungem
Mannschaftzahl
x Poloposition
x Punke
x Reglemant
Rumanien         # Rumanien [en title] -> Rumänien [REDIRECT]
Taschenschitt    #  skip composite word Taschen schitt   [REDIRECT]
x Terminsüberschneidungen
Transcriptionsfaktor
Ultravioletteleskopen
ünernahm        # skip composite word üner nahm [Turkish name]
x Unternehmengesellschaft
X Wettkämpf



Äbtissingen
aktuelleste    # Leste is already in common25
akzeptziert    # Akzept is already in common15, but not 25
Andang         # Andang is a full word
angetriebendes # skip composite word angetrieben des
Gerichtsassesors ## potentially correct ?? 
Getraude
Legierungem
Poloposition # Polo + position
Punke        # title
Reglemant    # Mant is  a place in France (occurs in 15, not in 25)
Rumanien     # title
Teamm        # Tea + mm
Terminsüberschneidungen # xxx fugens
undn
Unternehmengesellschaft
Wettkämpf





# more FN
#  -> many of these occur of we go below 30 and add all the other stuff to make composite words ... 
Äbtissingen          # skip composite word Äbtissin gen
aktuelleste          # Aktuel + Leste [DE] = wustenwind
akzeptziert          # Akzept [DE] + ziert
Andang               # Ghalib Andang
angetriebendes       # skip composite word angetrieben des
austronesianischen   # austronesia nischen
behiel               # fix by not having 2word stuff in there : skip composite word be hiel
Beschleunigungtest   # Beschleunigung test
Freitagstainings     # Freitag [s] + Taining [s] -> chinese place
Gerichtsassesors     # Gerichtsassesor {m} [veraltend] --> potentially correct ??!!
Getraude             # skip composite word Get raude
Klassikation         # skip composite word Klassi kation
Kontinuitätkorrektur # xxx wrong no fugen-s
Langstreckenstests # xxx wrong fugen-s
Legierungem      # SPECIAL: skip composite word (2 letter) Legie + rung + em [Legie
Mannschaftzahl   # xxx wrong fugen-s
Poloposition     # Pol oposition
Punke            # Punke ist ein veralteter ... Begriff für eine Prostituierte.
Reglemant        # skip composite word Regle mant    # place in France
Rumanien         # Rumanien [en title] -> Rumänien [REDIRECT]
Taschenschitt    #  skip composite word Taschen schitt   [REDIRECT]
Teamm            # skip composite word Te amm   [[fix with not having 2word stuff in there]
Terminsüberschneidungen # xxx wrong fugen-s
Transcriptionsfaktor # Transcription +s+ faktor
undn            # Skip word according to German declension und + n
ünernahm        # skip composite word üner nahm [Turkish name]
Unternehmengesellschaft
Wettkämpf       # skip composite word Wett kämpf






== Evaluation ==

Out of all 47 wrong words (True), 17-25 could be retrieved within a total set
of 101 to 374 returned words, leading us to compute F-scores between 11.8 and
22.9 for different cases. We can achieve recall rates between 36 % and 53 % at
precision rates of 17% to 6.7 % respectively.

Using common_25.dic and default setting, the algorithm finds 493 words out of
which 26 are true errors and misses 16 words (recall = 62 %, precision = 5.3%).


