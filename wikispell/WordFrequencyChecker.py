#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
A class used for frequency-based word processing.

Use this class to identify potential candidates using find_candidates based on a given word.
Then use load_candidates to identify pages in the Wiki where these words occur.
Finally use checkit to go through the words.

"""

import re

import textrange_parser as ranges
import SpellcheckLib

## pywikibot imports
try:
    import wikipedia as pywikibot
    import pagegenerators
    newBot = False
except ImportError:
    import pywikibot
    from pywikibot import pagegenerators
    newBot = True

hspell = None
try:
    import hunspell
    hspell = hunspell.HunSpell("/usr/share/hunspell/de_DE" + ".dic", "/usr/share/hunspell/de_DE" + ".aff")
except Exception:
    pass

class WordFrequencyChecker():

    def __init__(self, load=True):
        self.noall = []

    #
    ## Find and evaluate Levenshtein candidates
    # 
    def find_candidates(self, myw, cursor, 
                        occurence_cutoff = 20, lcutoff = 0.8,
                        db_='hroest.countedwords', ldistance = 6, applyFilter=True):
        """
        Find candidate misspellings for the input (correct) myw 

        Searches for all words starting with the same 3 characters in
        Wikipedia, then selects candidates among those with a Levenshtein ratio
        of less than the given cutoff. Also the word occur less than
        occurence_cutoff to be considered a candidate.
        """

        import Levenshtein

        # \xc2\xad is a soft hyphen that is sometimes used instead of a space

        # 1. Search for all words that start with the same 3 chars
        sterm = myw[:3]
        l = len(myw)
        cursor.execute(
        """
        select * from %s where smallword like '%s'
        #and length(smallword) between %s and %s
        and smallword not like '%s'
        and occurence < %s
        order by smallword
        """ % (db_, sterm.encode('utf8')+'%', l-2, l+2, myw.encode('utf8')+'%' , occurence_cutoff))
        similar = cursor.fetchall()

        # 2 Select candidates that have a Levenshtein ratio less than the cutoff
        candidates = [s[1] for s in similar if 
                      Levenshtein.ratio(myw,s[1].decode('utf8')) > lcutoff and
                      Levenshtein.distance(myw,s[1].decode('utf8')) < ldistance and
                      not '\xc2\xad' in s[1]] 

        if False and len(myw) > 9:
                sterm = "%" + myw[ 3:7] + "%"
                cursor.execute(
                """
                select * from %s where smallword like '%s' 
                #and length(smallword) between %s and %s
                and smallword not like '%s'
                and occurence < %s
                order by smallword 
                """ % (db_, sterm.encode('utf8'), l-2, l+2, myw.encode('utf8')+'%', occurence_cutoff) )
                similar = cursor.fetchall()

                
        # 3. Search for all words that start with the same char and end with the same 3 chars
        sterm = myw[0] + '%' + myw[-3:]
        cursor.execute(
        """
        select * from %s where smallword like '%s' 
        #and length(smallword) between %s and %s
        and smallword not like '%s'
        and occurence < %s
        order by smallword 
        """ % (db_, sterm.encode('utf8')+'%', l-2, l+2, myw.encode('utf8')+'%', occurence_cutoff) )
        similar = cursor.fetchall()

        # 4 Select candidates that have a Levenshtein ratio less than the cutoff
        candidates.extend(  [s[1] for s in similar if 
                      Levenshtein.ratio(myw,s[1].decode('utf8')) > lcutoff and
                      Levenshtein.distance(myw,s[1].decode('utf8')) < ldistance  and
                      not '\xc2\xad' in s[1]] )

        # Remove certain candidates 
        candidates = [c for c in candidates if c.find(")") == -1 and c.find("(") == -1 ]
        candidates = [c for c in candidates if c.decode("utf8").find(u"´") == -1 and 
                                               c.decode("utf8").find(u"‡") == -1 and
                                               c.decode("utf8").find(u"”") == -1 and
                                               c.decode("utf8").find(u"™") == -1 and
                                               c.decode("utf8").find(u"…") == -1 ]

        # 5 Remove candidates that are correctly spelled
        if hspell is not None:
            candidates = [c for c in candidates if not hspell.spell( c )]

        # 6 Check for similar things in the database (capitalization)
        final_candidates = []
        for cand in candidates:
                q = "select occurence, smallword from %s where smallword = '%s';"  % (db_, cand)
                try:
                    cursor.execute(q)
                except Exception:
                    # not properly escaped string ... 
                    continue
                nr = -1
                for res in cursor.fetchall():
                    if res[1].decode("utf8").lower() == cand.decode("utf8").lower():
                        if res[0] > nr:
                            nr = res[0]
                # print "check ", cand, nr
                if nr < occurence_cutoff:
                    final_candidates.append(cand)

        print "Removed %s due to high occurence in the word count" % ( len(candidates) - len(final_candidates) )
        candidates = final_candidates

        # 7 Remove possibly correct candidates
        if applyFilter:
            if myw.endswith("em") or \
               myw.endswith("es") or \
               myw.endswith("er") or \
               myw.endswith("en"): 
                    final_candidates = [cand for cand in final_candidates
                       if myw[-2:] == cand.decode("utf8")[-2:] or 
                          not (cand.endswith("em") or 
                               cand.endswith("es") or 
                               cand.endswith("er") or 
                               cand.endswith("en") ) ]

        # Get unique candidates sorted by ratio
        final_candidates = list(set(final_candidates))
        final_candidates.sort(lambda x,y: cmp( Levenshtein.ratio(myw,x.decode('utf8')), Levenshtein.ratio(myw,y.decode('utf8')) ) )


        # print "sorted"
        # for w in final_candidates:
        #         print w, Levenshtein.distance(myw,w.decode('utf8')) ,  Levenshtein.ratio(myw,w.decode('utf8'))

        return final_candidates

    def _load_candidates(self, correct, candidates, max_cand=120):

        pages = []
        for i, wrong in enumerate(candidates):

            wrong = wrong.decode('utf8')
            if correct.find(wrong) != -1: 
                continue
            if wrong in self.noall: 
                continue

            if newBot:
                searchResult = list(pagegenerators.SearchPageGenerator(wrong, namespaces='0', total=max_cand))
            else:
                searchResult = list(pagegenerators.SearchPageGenerator(wrong, namespaces='0'))

            print wrong, len(list(searchResult))
            if len(list(searchResult)) > max_cand:
                searchResult = list(pagegenerators.SearchPageGenerator("%s" % wrong, namespaces='0'))
                print "now we have ", len(searchResult), " found"

            if len(list(searchResult)) > max_cand:
                searchResult = searchResult[:10]

            for p in searchResult:
                p.wrong = wrong;
                p.words = [ SpellcheckLib.WrongWord(wrong, bigword=wrong, correctword=correct) ]
                print "append page", p
                pages.append(p)

        return pages

    def load_candidates(self, correct, candidates, askUser=True):

        if not askUser:
            return self._load_candidates(correct, candidates)

        print "Enter numbers separated with a space" 
        for i, wrong in enumerate(candidates): 
            wrong = wrong.decode('utf8')
            if wrong in self.noall:
                continue
            if correct.find(wrong) != -1:
                continue
            print i, wrong
        
        print "Enter * to switch to positive selection" 
        toignore = pywikibot.input('Ignore?')

        # Allow early out
        if toignore.strip() == "x":
            return []

        # Allow positive selection (select only words)
        if toignore.strip() == "*":
            toignore = pywikibot.input('Select only?')
            try:
                select_only = [t for t in toignore.split(' ') if t != '']
                res = []
                for sel in select_only:
                    try:
                        res.append( int(sel) )
                    except ValueError:
                        spl = sel.split("-")
                        if len(spl) == 2:
                            print "got split", spl
                            res.extend( range(int(spl[0]), int(spl[1])+1) )

                print "selected", res

                tmp = [candidates[int(t)] for t in res]
                candidates = tmp
            except ValueError, IndexError:
                pass
        else:
            # Negative selection (ignored words)
            try:
                toignore = [candidates[int(t)].decode('utf8') for t in toignore.split(' ') if t != '']
            except ValueError, IndexError:
                pass

            self.noall.extend(toignore)

        return self._load_candidates(correct, candidates)

