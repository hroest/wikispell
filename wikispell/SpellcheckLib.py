#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
A library of spellchecking helper classes and functions
"""

#
# Distributed under the terms of the MIT license.
#

## pywikibot imports
import time, sys
import re, string
import wikipedia as pywikibot
import pagegenerators
import textrange_parser
import codecs

class Word(object):

    def __init__(self, text):
        self.word = text
        self.suggestions = None

    def __str__(self):
        return self.word

    def __len__(self):
        return len(self.word)

    def __cmp__(self,other):
        return self.word.__cmp__(str(other))

    def derive(self):
        # Get the short form of the word, without punctuation, square
        # brackets etcetera
        shortword = self.word
        # Remove all words of the form [[something:something - these are
        # usually interwiki links or category links
        if shortword.rfind(':') != -1:
            if -1 < shortword.rfind('[[') < shortword.rfind(':'):
                shortword = ""
        # Remove barred links
        if shortword.rfind('|') != -1:
            if -1 < shortword.rfind('[[') < shortword.rfind('|'):
                shortword = shortword[:shortword.rfind('[[')] + shortword[
                    shortword.rfind('|') + 1:]
            else:
                shortword = shortword[shortword.rfind('|') + 1:]
        shortword = shortword.replace('[', '')
        shortword = shortword.replace(']', '')
        #replace all occurencs of &nbsp;
        shortword = shortword.replace('&nbsp;', ' ')
        shortword = shortword.replace('nbsp;', ' ')
        # Remove non-alphanumerical characters at the start
        try:
            while shortword[0] in string.punctuation + u'«»–−→“„‚‘’':
                shortword = shortword[1:]
        except IndexError:
            return ""
        # Remove non-alphanumerical characters at the end; no need for the
        # try here because if things go wrong here, they should have gone
        # wrong before
        while shortword[-1] in string.punctuation + u'«»–−→“„‚‘’':
            shortword = shortword[:-1]
        # Do not check URLs
        if shortword.startswith("http://") or shortword.startswith("https://") or shortword.startswith("www."):
            shortword=""
        # Do not check 'words' with only numerical characters
        number = True
        for i in xrange(len(shortword)):
            if not (shortword[i] in string.punctuation or
                    shortword[i] in string.digits):
                number = False
        if number:
            shortword = ""
        return shortword

    def replace(self, rep):
        """Replace the short form by 'rep'. Keeping simple for now - if the
        short form is part of the long form, replace it. If it is not, ask the
        user

        """
        if rep == self.derive():
            return self.word
        if self.derive() not in self.word:
            return pywikibot.input(
                u"Please give the result of replacing %s by %s in %s:"
                % (self.derive(), rep, self.word))
        return self.word.replace(self.derive(), rep)

    def isCorrect(self, checkalternative=False):
        """If checkalternative is True, the word will only be found incorrect
        if it is on the spelling list as a spelling error. Otherwise it will be
        found incorrect if it is not on the list as a correctly spelled word.

        """
        if self.word == "":
            return True
        if self.word in pageskip:
            return True
        try:
            if knownwords[self.word] == self.word:
                return True
            else:
                return False
        except KeyError:
            pass
        if self.word != uncap(self.word):
            return Word(uncap(self.word)).isCorrect(
                checkalternative=checkalternative)
        else:
            if checkalternative:
                if checklang == 'nl' and self.word.endswith("'s"):
                    # often these are incorrect (English-style) possessives
                    return False
                if self.word != cap(self.word):
                    if Word(cap(self.word)).isCorrect():
                        return False
                    else:
                        return True
                else:
                    return True
            else:
                return False

    def getAlternatives(self):
        if not self.suggestions is None: return self.suggestions
        alts = []
        if self.word[0].islower():
            if Word(cap(self.word)).isCorrect():
                alts = [cap(self.word)]
        try:
            alts += knownwords[self.word]
        except KeyError:
            pass
        if self.word[0].isupper():
            try:
                alts += [cap(w) for w in knownwords[uncap(self.word)]]
            except KeyError:
                pass
        return [a.replace('_',' ') for a in alts]

    def declare_correct(self):
        knownwords[self.word] = self.word

    def declare_alternative(self, alt):
        if not alt in knownwords[self.word]:
            knownwords[self.word].append(word)
            newwords.append(self.word)
        return self.alternatives

class WrongWord(Word):

    def __init__(self, wrong_word, location=-1, bigword='', correctword='',
                doReplace=False):
        self.location = location
        self.bigword = bigword
        self.correctword = correctword
        self.doReplace = doReplace

        Word.__init__(self, wrong_word)

class CallbackObject(object):
    """ Callback object """
    def __init__(self):
        pass

    def __call__(self, page, error, optReturn1 = None, optReturn2 = None):
        self.page = page
        self.error = error
        self.optReturn1 = optReturn1
        self.optReturn2 = optReturn2

def findRange(opening, closing, text, start=0, alternativeBreak = None,
             ignore_in = [] ):
    """ Wrapper around textrange parser 
    """
    res = textrange_parser.findRange(opening, closing, text, start, alternativeBreak,
             ignore_in)
    return [res.ranges, [res.match, res.not_matching] ]

class abstract_Spellchecker(object):
    """
    Base class for various spellcheckers
    """

    def forbiddenRanges(self, text, removeNested=True, mergeRanges=True, level="full"):
        """ Identify ranges where we do not want to spellcheck.

        These ranges include templates, wiki links, tables etc
        """

        ran = []
        albr = ['</ref', '\n', '}}'] # alternative breaks
        extrabr = ['"', "'", u'\u201d', u'\u201c'] # extra breaks

        ran.extend(findRange('{{', '}}', text)[0] )      #templates
        ran.extend(findRange('[[', ']]', text)[0] )      #wiki links

        ran.extend(findRange(u'{|', u'|}', text)[0] )    #tables

        # Quotation marks
        # See https://de.wikipedia.org/wiki/Anf%C3%BChrungszeichen#Kodierung

        # Simple quotation marks
        ran.extend(findRange('\"', '\"', text,
            alternativeBreak = albr + extrabr)[0] )

        # French quotation marks
        ran.extend(findRange(u'«', u'»', text,
            alternativeBreak = albr)[0] )

        # Double quotation marks German: „“ ->  \u201e and \u201c
        ran.extend(findRange(u'\u201e', u'\u201c', text,
            alternativeBreak = albr + extrabr)[0] )

        #  -> also do the above without the extra breaks as to not abort early
        ran.extend(findRange(u'\u201e', u'\u201c', text,
             alternativeBreak = albr)[0] )
        ran.extend(findRange('\"', '\"', text,
            alternativeBreak = albr)[0] )

        ran.extend(findRange('\'\'', '\'\'', text,
            alternativeBreak = albr)[0] )                #italic

        ran.extend(findRange('\'\'\'', '\'\'\'', text,
            alternativeBreak = albr)[0] )                #bold

        ran.extend(findRange('<!--', '-->', text)[0] )   #comments

        # Regex-based ranges ... 
        ran.extend( textrange_parser.hyperlink_range(text) )
        #ran.extend( textrange_parser.picture_range(text) )       #everything except caption
        ran.extend( textrange_parser.regularTag_range(text) )     #all tags specified
        ran.extend( textrange_parser.sic_comment_range(text) )    #<!--sic-->

        if level == "full":
            ran.extend( textrange_parser.references_range(text) )     #all reftags
            ran.extend( textrange_parser.list_ranges(text) )          # lists

        # Remove trailing text at the end (references, weblinks etc)
        if level == "full":
            mm = re.search("==\s*Weblinks\s*==", text)
            if mm: ran.append( [mm.start(), len(text)] )

            mm = re.search("==\s*Quellen\s*==", text)
            if mm: ran.append( [mm.start(), len(text)] )

            mm = re.search("==\s*Einzelnachweise\s*==", text)
            if mm: ran.append( [mm.start(), len(text)] )

            mm = re.search("\[\[Kategorie:", text)
            if mm: ran.append( [mm.start(), len(text)] )

        if removeNested:
            ran = self.remove_nested_ranges(ran)

        if mergeRanges:
           ran = self.merge_ranges(ran)

        return ran

    def merge_ranges(self, ran):
        tmp = []

        if len(ran) == 0:
            return ran

        ran = sorted(ran)

        tmp.append(ran[0])
        j = 0
        i = 1
        while i < len(ran):

            # Candidate for merge
            if tmp[j][1] + 1 >= ran[i][0] and \
               ran[i][1] > tmp[j][1]:
                tmp[j][1] = ran[i][1]
            else:
                tmp.append(ran[i])
                j = j+1

            i = i+1

        return tmp

    def remove_nested_ranges(self, ran):

        def range_is_subset(ranges, r):
            for riter in ranges:
                if r[0] >= riter[0] and r[1] <= riter[1]:
                    return True
            return False

        ranges = []
        for r in sorted(ran):
            if not range_is_subset(ranges, r):
                ranges.append(r)

        return ranges

    def check_in_ranges(self, ranges, wordStart, wordEnd, curr_r, loc):
        """ Check for the next skippable range and move loc across it.

        Args:
            ranges( list(pair)) : a list of ranges (a pair of start/end
                                  position) which should be skipped
            wordStart(int) : a start position of the current word
            wordEnd(int) : an end position of the current word
            curr_r(int) : current range pointer
            loc(int) : current text cursor position 

        Returns:
            tuple(curr_r, loc, current_context)
            - curr_r: this contains the new current range pointer (which range is current)
            - loc: this contains the new current text cursor
            - current_context: True if context should be skipped, False otherwise
        """
       
        wordMiddle = 0.5*(wordStart + wordEnd)

        # Check if the current match is contained in the next range 
        if curr_r < len(ranges) and \
          ( (ranges[curr_r][0] <= wordMiddle and ranges[curr_r][1] > wordMiddle) or \
            (ranges[curr_r][0] <= loc and ranges[curr_r][1] > loc) ):

            # Update the current location to the end of the range
            loc = ranges[curr_r][1]

            # Choose location as end of next range while location is smaller
            # than the start of the range
            while curr_r < len(ranges) and ranges[curr_r][0] < loc:

                # Only update location if the new location would be larger
                if loc < ranges[curr_r][1]:
                    loc = ranges[curr_r][1]

                curr_r += 1

            return curr_r, loc, True

        # Check if current range needs to be advanced

        is_advanced = False
        while curr_r < len(ranges) and ranges[curr_r][0] < loc:
            curr_r += 1

            # Advance location if necessary
            if curr_r < len(ranges) and \
              ( (ranges[curr_r][0] <= wordMiddle and ranges[curr_r][1] > wordMiddle) or \
                (ranges[curr_r][0] <= loc and ranges[curr_r][1] > loc) ):

                # Update the current location to the end of the range
                loc = ranges[curr_r][1]
                is_advanced = True

        # Also return true if we advanced the ptr
        if is_advanced:
            return curr_r, loc, True

        # Else, return the input parameters and 
        return curr_r, loc, False

class InteractiveWordReplacer(abstract_Spellchecker):
    """ Interactivly replace individual words

    The main function is processWrongWordsInteractively which takes a list of
    page objects, each of which has a list of "WrongWord" objects attached to
    it. These objects describe which words need to be replaced on the page in
    question.
    """

    def __init__(self, xmldump=None):
        self.ignorePages = []
        self.ignorePerPages = {}
        self.dontReplace = []

        self.Callbacks = []

    def processWrongWordsInteractively(self, pages, offline=False):
        """This will process pages with wrong words.

        It expects a list of pages with words attached to it.
        """

        self.performReplacementList = []
        ask = True
        gen = pagegenerators.PreloadingGenerator(pages)
        for page in gen:
            print('Processing Page = %s'% page.title() )
            thisReplace = []
            try:
                text = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist, skip!" % page.title())
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect, get target!" % page.title())
                oldpage = page
                page = page.getRedirectTarget()
                page.words = oldpage.words
                text = page.get()

            text = page.get()
            self.dontReplace = self._checkSpellingInteractive(page, self.dontReplace)
            newtext = self._doReplacement(text, page)

            if text == newtext: 
                continue

            pywikibot.showDiff(text, newtext)
            if ask: choice = pywikibot.inputChoice('Commit?',
               ['Yes', 'yes', 'No', 'Yes to all'], ['y', '\\', 'n','a'])
            else: choice = 'y'
            #if choice == 'a': stillAsk=False; choice = 'y'
            if choice in ('y', '\\'):
                callb = CallbackObject()
                self.Callbacks.append(callb)
                page.put_async(newtext, comment=page.typocomment, callback=callb)

    def _checkSpellingInteractive(self, page, dontReplace):
        """Interactively goes through all wrong words in a page.

        All we do here is save doReplace = True if we want to replace it, while
        doReplace will do the actual replacement.
        Uses self.ignorePerPages and a local dontReplace
        """

        title = page.title()
        text = page.get()
        words = page.words
        for w in words: 
            w.doReplace = False

        # Go through all wrong words in this page
        for w in words:
            smallword = w.word

            # Check if on ignore list -> continue
            if self.ignorePerPages.has_key(title) \
               and smallword in self.ignorePerPages[title]: 
                continue
            if smallword in dontReplace:
                if self.ignorePerPages.has_key( title ):
                    self.ignorePerPages[title].append( smallword)
                else: 
                    self.ignorePerPages[ title ] = [ smallword ]
                continue

            bigword = Word(w.bigword)
            loc = w.location

            # Try to find replacement site
            w.site = text.find(bigword.word, loc)
            if w.site == -1: 
                w.site = text.find(bigword.word)
            if w.site == -1: 
                pywikibot.output(u"Not found any more in %s: %s" % (
                title, bigword.word))
                continue

            # We now have a potential site for replacement
            sugg = w.correctword
            w.LocAdd = len(bigword)

            # Check if the word has been replaced in the meantime with the
            # correct suggestion
            if len(text) > loc + len(sugg) and \
              text[w.site:w.site+len(sugg)].lower() == sugg.lower():
                continue
            if smallword == sugg: 
                continue

            # Adjust case
            if smallword[0].isupper(): 
                sugg = sugg[0].upper() + sugg[1:]

            # Print the two words
            pywikibot.output(u"Replace \03{lightred}\"%s\"" % smallword +
              "\03{default} \nby      \03{lightgreen}\"%s\"\03{default}" % sugg)

            # Print context
            pywikibot.output(u"    %s" % text[max(0,w.site-55):w.site+len(w)+55])
            choice = pywikibot.inputChoice('', ['Yes', 'yes', 'No', 'no',
               'No but dont save', 'never replace' 'Replace by something else',
                'Exit and go to next site'], ['y', '\\', 'n', ']', 'b', 'v', 'r', 'x'])

            # Evaluate user choice
            if choice == 'b':
                continue
            if choice in ('v'): 
                dontReplace.append(w.word) 
                if self.ignorePerPages.has_key( title ):
                    self.ignorePerPages[title].append( smallword)
                else: self.ignorePerPages[ title ] = [ smallword ]
            if choice in ('n', ']'): 
                if self.ignorePerPages.has_key( title ):
                    self.ignorePerPages[title].append( smallword)
                else: self.ignorePerPages[ title ] = [ smallword ]
                continue
            if choice == 'x': 
                self.ignorePages.append( title );
                return dontReplace
            if choice == 'r':
                w.replacement = pywikibot.input(u"What should I replace \"%s\" by?"
                                              % bigword.word)
                w.doReplace = True
            if choice in ( 'y','\\'):
                w.replacement = bigword.replace(sugg)
                w.doReplace = True

        return dontReplace

    def _doReplacement(self, text, page, ask = True):
        """This will perform the replacement for one page and return the text.
        """

        page.typocomment  = u"Tippfehler entfernt: "

        #now we have the text, lets replace the word
        for i, word in enumerate(page.words):
            if not word.doReplace: 
                continue

            self.performReplacementList.append(word)

            # Try to find replacement site (text may have changed in the meantime)
            site = text.find( word.bigword, word.site )
            if site == -1:
                site = text.find( word.bigword )
            if site == -1: 
                continue

            # now we have the site (page might be changed in meantime)
            loc = site
            replacement = word.replacement
            LocAdd = word.LocAdd

            # Check for cases where the the wrong word is contained in the
            # replacement but already corrected (this may happen if somebody
            # has replaced the text in the meantime). 
            # We would still find the wrong word but should not replace it!
            replacementHere = text.find( replacement )
            while not replacementHere == site and not replacementHere == -1:
                replacementHere = text.find( replacement , replacementHere+1)

            # exclude cases where replacement is contained in wrong word
            if replacementHere == site and word.bigword.find(replacement) == -1:
                continue

            # Replace the text
            text = text[:loc] + replacement + text[loc+LocAdd:]

            if i > 0: 
                page.typocomment += " , "
            page.typocomment += word.word + " => " + word.replacement

        return text

def readBlacklist(filename, badDict, encoding="utf8"):
    """
    Read in a list of wrong words
    """
    f = codecs.open(filename, 'r', encoding = encoding)
    for line in f.readlines():
        # remove trailing newlines and carriage returns
        try:
            while line[-1] in ['\n', '\r']:
                line = line[:-1]
        except IndexError:
            pass
        #skip empty lines
        if line != '':
            line = line.split(';')
            badDict[ line[0].lower() ] = line[1]

def writeBlacklist(filename, encoding, badDict):
    """
    Write out a list of wrong words
    """
    f = codecs.open(filename, 'w', encoding = encoding)
    for key in sorted(badDict.keys()):
        f.write('%s;%s\n' % (key, badDict[key]))
    f.close()

if __name__ == "__main__":
    pass
