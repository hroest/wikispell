
You can use the testfiles in tests/data/check500.tar.gz and
tests/data/check250.tar.gz to evaluate the spellchecker. Unpack them to a
directory and store their paths in a file, then run the hunspell checker:

tar xzvf tests/data/check500.tar.gz 
tar xzvf tests/data/check250.tar.gz 
mv check500/ /tmp/
mv check250/ /tmp/
ls /tmp/check500/* > /tmp/filepaths
ls /tmp/check250/* >> /tmp/filepaths

$ python spellcheck_hunspell.py -dictionary:/usr/share/hunspell/de_DE_frami_nhr \
    -common_words:../spellcheck-data/lists/de/common_15.dic
    -textfiles:/tmp/filepaths 

cat tests/data/wrong_words.txt | sort > /tmp/wrong
grep '*99' output_all25 | cut -f 2 -d ' ' | sort > /tmp/found
wc /tmp/found
comm -32 /tmp/wrong /tmp/found  | wc # false negatives

One of the main challenges remains the low precision which means many correct
words will be marked as incorrect. If you run the hunspell checker with the
regular settings (de_DE_frami) and no other wordlist, then it will report the
following

945228 words checked
11076 words found needed checking (1.17 %)
4137 unique words found (0.438 %)
2978 words with a single occurrence (0.315 %)
2978 words with a single occurrence (0.315 %)
42 words are truly incorrect  (0.0044 % of total, 1.02 % of found words)
-> computed F1-score of 0.02 with 100% recall and 1.02 % precision


At the cost of lower recall, we can increase the F1 score from around 2% 





time python spellcheck_hunspell.py -dictionary:/usr/share/hunspell/de_DE_frami_nhr -common_words:'../spellcheck-data/output_en.txt;../spellcheck-data/output_de.txt;../spellcheck-data/lists/de/common_15.dic'  -textfiles:/tmp/filepaths > output__ende_titles_all15_filter4


bash evaluate.sh output__ende_titles_all15_filter4
# 118 total / 10 TP

# 155 total / 14 TP


# 330 total / 22 TP

### F = 15.2
# 129 total / 13 TP

recall  = 13 /42.0
precision = 13 / 129.0

# 125 total  / 11 TP

# 131 total  / 13 TP
## 131 / 28 == 131 total / 14 TP

2 * precision * recall / (precision + recall)


###  stringent:0, remove < 3, filter <4
## 162 / 25 == 162 total / 17 TP
# F = 16.6


# stringent 61: 
## 1009  / 3 == 1009 total / 39 TP
# F = 7.42
-> only 3 FN, which are all articles in DE-wiki
# Andang
# Punke
# Rumanien

# stringent 59: 
## 377  / 16 == 377 total / 26 TP
# F = 12.4
# -> already 16 FN, based on common words: 

### Äbtissingen
### aktuelleste
### akzeptziert
### Andang
### angetriebendes
### Beschleunigungtest
### Getraude
### Kontinuitätkorrektur
### Langstreckenstests
### Legierungem
### Mannschaftzahl
### Poloposition
### Punke
### Terminsüberschneidungen
### Unternehmengesellschaft
### Wettkämpf


# stringent 57: 
## 218  / 22 == 218 total / 20 TP
# F = 15.4
## has now 22 FN

# stringent 54: 
## 162  / 25 == 162 total / 17 TP
# F = 16.6
## has now 22 FN

# stringent 49: 
## 134  / 28 == 134 total / 14 TP
# F = 16.2

# stringent 49: _filter
## 275  / 17 == 275 total / 25 TP
# F = 15.77   -> F score improves substantially from 59 due to filtering!!

# stringent 49: _filter
## 269  / 18 == 269 total / 24 TP
# 

# stringent 49: _filter -> use CC also for composite words
## 220  / 21 == 220 total / 21 TP
# F = 16.03

# stringent 49: _filter -> use CC also for composite words
## 209  / 21 == 209 total / 21 TP
# F = 16.73

# stringent 49: _filter -> use CC also for composite words
## 200  / 24 == 200 total / 18 TP

# stringent 49: _filter -> use CC also for composite words
## 208  / 21 == 208 total / 21 TP

 ## after fixing fugen s
# stringent 49: _filter -> use CC also for composite words
## 212  / 20 == 212 total / 22 TP

## after fixing fugen s second time! 
# stringent 49: _filter -> use CC also for composite words
## 216  / 18 == 216 total / 24 TP
# F = 18.6

## 217  / 17 == 217 total / 25 TP
# F = 19.3

## 219  / 17 == 219 total / 25 TP
# F = 19.2
#  precision ~ 11.4%

# minlen = 3
## 293  / 12 == 293 total / 30 TP
# F = 17.9
#  precision ~ 10%


# also switch to upper/lower distinction in decl in filter words ... 
## 227  / 16 == 227 total / 26 TP
# F = 19.3
#  precision ~ 11.4%

# ml2
## 241  / 14 == 241 total / 28 TP
# F = 19.8
#  precision ~ 11.6%

# no cc dict
## 276  / 12 == 276 total / 30 TP
# F = 18.9
#  precision ~ 10.9%






# use all dicts, stringent 49, use nhr5
## 174  / 18 == 174 total / 24 TP
# F = 22.2 % 
#  precision ~ 13.8%


# use all dicts, stringent 49, use nhr, comm15
## 199  / 17 == 199 total / 25 TP
# F = 20.7 % 
#  precision ~ 12.6%

### try different common words ... default is 15

# use all dicts, stringent 49, use nhr, comm25
## 226  / 17 == 226 total / 25 TP
# F = 18.7 %
#  precision ~ 11.1 %

# use all dicts, stringent 49, use nhr, comm10
## 176  / 21 == 176 total / 21 TP
# F = 19.3 %
#  precision ~ 11.9 %




# use all dicts, stringent 29, use nhr
## 151  / 22 == 151 total / 20 TP
# F = 20.7 % 
#  precision ~ 13.2 %


# use all dicts, stringent 29, use nhr_new
## 139  / 23 == 139 total / 19 TP
# F = 20.99 % 
#  precision ~ 13.7 %



# use all dicts, stringent 49, use nhr
## 199  / 17 == 199 total / 25 TP
# F = 20.7 % 
#  precision ~ 12.6%

# use all dicts, stringent 51, use nhr
## 224  / 15 == 224 total / 27 TP
# F = 20.3 % 
#  precision ~ 12.0%

# use all dicts, stringent 56, use nhr
## 260  / 14 == 260 total / 28 TP
# F = 18.5 % 
#  precision ~ 10.7%

# use all dicts, stringent 59, use nhr
## 310  / 14 == 310 total / 28 TP
# F = 15.9 % 
#  precision ~ 9.0%


####################################################
# Try to increase the number of TP by having some loss in precision
# It seems the best result > 25 TP can be achieved with using comm1

# use all dicts, stringent 59, use nhr_new, comm15, minl4
## 588  / 6 == 588 total / 36 TP
# F = 11.4 % 
#  precision ~ 6.1%

# use all dicts, stringent 51, use nhr_new, comm15, ml3
## 280  / 13 == 280 total / 29 TP
# F = 18.0 % 
#  precision ~ 11.9%

# use all dicts, stringent 51, use nhr_new, comm15
## 218  / 16 == 218 total / 26 TP
# F = 20.0 % 
#  precision ~ 11.9%

# use all dicts, stringent 51, use nhr_new, comm25
## 307  / 13 == 218 total / 29 TP
# F = 
#  precision ~ 


# use all dicts, stringent 59, use nhr_new, comm15, minl3
## 416  / 10 == 416 total / 32 TP
# F = 13.9 % 
#  precision ~ 7.7%



####################################################
# try to use different common dicts, maximizing precision and F1 score:
## maximal precision = 21.9 % 
## maximal F1 score = 27.03 % 


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
$ sed -r '/^.{,9}$/d' lists/de/common_2.dic > /tmp/common2_filter9.dic
$ sed -r '/^.{,6}$/d' lists/de/common_5.dic > /tmp/common5_filter6.dic
$ sed -r '/^.{,9}$/d' lists/de/common_2.dic > /tmp/common2_filter9.dic
$ sed -r '/^.{,4}$/d' lists/de/common_15.dic > /tmp/common15_filter4.dic
$ cat lists/de/common_25.dic /tmp/common5_filter6.dic /tmp/common2_filter9.dic /tmp/common15_filter4.dic | sort | uniq  > /tmp/common_merge.dic

$ sed -r '/^.{,11}$/d' lists/de/common_2.dic > /tmp/common2_filter11.dic
$ sed -r '/^.{,7}$/d' lists/de/common_5.dic > /tmp/common5_filter7.dic
$ sed -r '/^.{,5}$/d' lists/de/common_15.dic > /tmp/common15_filter5.dic
$ sed -r '/^.{,3}$/d' lists/de/common_25.dic > /tmp/common25_filter3.dic
$ cat lists/de/common_50.dic /tmp/common25_filter3.dic /tmp/common15_filter5.dic \
    /tmp/common5_filter7.dic /tmp/common2_filter11.dic  | sort | uniq  > /tmp/common_merge_str.dic

$ wc /tmp/common_merge*
  2387217  2387267 33878888 /tmp/common_merge.dic
  2070885  2070923 30453210 /tmp/common_merge_str.dic
  4458102  4458190 64332098 total
$ wc lists/de/common_*
   908518    908535  10867473 lists/de/common_10.dic
   680225    680232   8027155 lists/de/common_15.dic
   457613    457615   5312853 lists/de/common_25.dic
  3054938   3055444  39307554 lists/de/common_2.dic
   285153    285154   3246137 lists/de/common_50.dic
  1488964   1489026  18307850 lists/de/common_5.dic
  6288826   6292750  84981021 lists/de/common_all.dic
 13164237  13168756 170050043 total


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



== New idea: filtering ==

sed -r '/^.{,6}$/d' lists/de/common_5.dic > /tmp/common5_filter6.dic
sed -r '/^.{,9}$/d' lists/de/common_2.dic > /tmp/common2_filter9.dic
sed -r '/^.{,4}$/d' lists/de/common_15.dic > /tmp/common15_filter4.dic
sed -r '/^.{,3}$/d' lists/de/common_25.dic > /tmp/common25_filter3.dic
sed -r '/^.{,5}$/d' lists/de/common_15.dic > /tmp/common15_filter5.dic
sed -r '/^.{,7}$/d' lists/de/common_5.dic > /tmp/common5_filter7.dic
sed -r '/^.{,11}$/d' lists/de/common_2.dic > /tmp/common2_filter11.dic
sed -r '/^.{,3}$/d' lists/de/common_25.dic > /tmp/common25_filter3.dic
sed -r '/^.{,3}$/d' lists/de/common_25.dic > /tmp/common25_filter3.dic

cat lists/de/common_50.dic /tmp/common25_filter3.dic /tmp/common15_filter5.dic  /tmp/common5_filter7.dic /tmp/common2_filter11.dic  | sort | uniq  > /tmp/common_merge_str.dic


time python spellcheck_hunspell.py -dictionary:../spellcheck-data/hunspell/de_DE_frami_new  -common_words:'/tmp/common_merge_str.dic' -stringent:49 -nosugg   -textfiles:/tmp/filepaths > output_str49_commmerge_minl0_newn_str_trial2

