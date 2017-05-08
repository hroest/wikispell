#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
A base class for different spellcheckers
"""

#
# Distributed under the terms of the MIT license.
#

import time, sys
import re, string
import textrange_parser

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

        level is one of [none, relaxed, fast, wiki-skip, full]:

            none: do not remove any text
            relaxed: remove templates, tables, links, comments, italic, bold, tags, hyperlinks 
            fast: same as relaxed
            wiki-skip: skip additional wiki syntax (including reftags)
            full: also remove text in quotation marks, lists, trailing text (after weblinks)

            moderate-legacy: legacy mode that is the same as relaxed but also removes
                words inside quotation marks (single, French, German)

        """

        if level == "none":
            return []

        st = time.time()
        ran = []
        albr = ['</ref', '\n', '}}'] # alternative breaks
        extrabr = ['"', "'", u'\u201d', u'\u201c'] # extra breaks

        ran.extend(findRange('{{', '}}', text)[0] )      #templates
        ran.extend(findRange('[[', ']]', text)[0] )      #wiki links
        ran.extend(findRange('<!--', '-->', text)[0] )   #comments

        ran.extend(findRange(u'{|', u'|}', text)[0] )    #tables

        # Quotation marks
        # See https://de.wikipedia.org/wiki/Anf%C3%BChrungszeichen#Kodierung

        if level in ["full", "moderate-legacy"]:
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

        # Regex-based ranges ... 
        ran.extend( textrange_parser.hyperlink_range(text) )
        #ran.extend( textrange_parser.picture_range(text) )       #everything except caption
        ran.extend( textrange_parser.regularTag_range(text) )     #all tags specified
        ran.extend( textrange_parser.sic_comment_range(text) )    #<!--sic-->

        if level in ["full", "wiki-skip"]:
            ran.extend( textrange_parser.references_range(text) )     #all reftags
        if level == "full":
            ran.extend( textrange_parser.list_ranges(text) )          # lists

        # Remove trailing text at the end (references, weblinks etc)
        if level == "full":
            mm = re.search("==\s*Weblinks\s*==", text)
            if mm: ran.append( [mm.start(), len(text)] )

            mm = re.search("==\s*Quellen\s*==", text)
            if mm: ran.append( [mm.start(), len(text)] )

            mm = re.search("==\s*Einzelnachweise\s*==", text)
            if mm: ran.append( [mm.start(), len(text)] )

            mm = re.search("==\s*References\s*==", text)
            if mm: ran.append( [mm.start(), len(text)] )
 
            mm = re.search("==\s*Further reading\s*==", text)
            if mm: ran.append( [mm.start(), len(text)] )
 
            mm = re.search("==\s*External links\s*==", text)
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

if __name__ == "__main__":
    pass
