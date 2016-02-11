#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
A library that deals with ranges in mediawiki texts.

The main methods are:
    findRange :  given an opening and closing argument (e.g. {{ and }}) it will
                 find all (also nested) ranges that are enclosed by the opening / 
                 closing string.
                 In addition, it accepts a start argument to design a starting
                 point and alternativeBreak argument to designate additional
                 closing points. Furthermore it allows to specify a list of
                 positions (list of integers) ignore_in where the opening / 
                 closing strings will be ignored if they are found at a
                 position contained in the ignore_in argument.
                 The function returns an object of type Ranges.

    find_next_unignored : The function finds the next occurence of pattern in
                 the given text, ignoring all occurences at positions indicated 
                 with ignores (a list of integers).

    split_with_ignores : Basically a text.split( separator ) method with the 
                only difference that it will not split at any position that 
                is contained in the this_ignores array

"""

import re

class Ranges:
    def __init__(self, ranges=[], match=True, not_matching=[]):
        self.ranges = ranges
        self.match  = match
        self.not_matching = not_matching

    def remove_last_range( self ):
        self.ranges = self.ranges[:-1]

    def get_large_ranges( self ):
        res = []
        for  i in self.ranges:
            res.extend( range( i[0], i[1] )  )
        return res

    def __iter__(self):
        return self.ranges

class PictureText:
    def __init__(self, start = -1, fulltext = '', elements = []): 
        self.start = start
        self.fulltext = fulltext
        self.elements = elements

def findRange(opening, closing, text, start=0, alternativeBreak = None,
             ignore_in = [] ):
    """Returns the range of all text between opening and closing statement.
    This also detects nested statements without restriction of depth
    The returned range starts at the first character of 'opening' and
    ends at the last character of 'closing'.

    The alternativeBreak argument allows to pass alternative breakpoints that
    are treated as if they were closing statements as well.
    """

    loc = start
    stack = []
    these_ranges = []
    closeOpenMatch = True
    notMatching = []
    while True:
        o = find_next_unignored(text, loc, opening, ignore_in )
        c = find_next_unignored(text, loc, closing, ignore_in )

        if alternativeBreak:
            this_min = len( text ) + 1; mini = -1
            # here we find the closest alternative breaking point that is
            # after the opening (or we already ARE after an opening,
            # indicated by something on the stack)
            for alt in alternativeBreak:
                alternativ_c = find_next_unignored(text, loc, alt, ignore_in)
                if (not alternativ_c == -1 and alternativ_c < this_min
                    and (alternativ_c > o or len(stack) > 0)   ):
                    this_min = alternativ_c; mini = alt
            
            # If we found an alternative breakpoint and it is before the next
            # closing statement (if there is one), use this as closing
            if not mini==-1 and (this_min < c or c==-1):
                c = this_min - len(closing)  + len(mini)

        # Here we found the next opening and closing statement
        # -> leave if we didn't find any closing match any more
        if c == -1: break;

        # Distinguish 3 cases:

        # Case 1: The next opening statement is before the next closing
        # statement, there are two possible explanations:
        # - there is another opening statement between the two (then we add one level of nesting)
        # - if not, we have found a range which we can append
        if o < c and not o == -1:
            next_open = find_next_unignored(text, loc + 1, opening, ignore_in )
            if next_open >= o and next_open < c:
                stack.append(o)
                loc = o + 1
            else: 
                these_ranges.append( [o, c+len(closing)] )
                loc = c+1

        # Case 2: The next closing statement is before the next opening
        # statement. This means that we can go back one level of nesting (or if
        # the stack is empty we have to add this closing statement as an
        # unmatched closing statement).
        elif c < o or o == -1:
            if len(stack) > 0:
                these_ranges.append([stack.pop(), c+len(closing)])
                loc = c + len(closing)
            else:
                closeOpenMatch = False;
                notMatching.append(c);
                loc = c + len(closing)

        # Case 3: The next closing and opening statements coincide (they are
        # the same).  This means we can go back one level of nesting if the
        # stack is not empty (treating it as a closing statement) or add one
        # level to the stack (treating it as an opening statement).
        elif c == o:
            if len(stack) > 0:
                these_ranges.append([stack.pop(), c+len(closing)])
                loc = c + len(closing)
            else:
                stack.append(o); loc = o + len(opening)

    # If the stack is not empty by now, we are missing at least one closing statement
    if not len(stack) == 0:
        closeOpenMatch = False;
        notMatching.extend(stack)

    # Create ranges object and store the ranges and the matches
    ranges = Ranges(ranges=these_ranges, match=closeOpenMatch, not_matching=notMatching)
    return ranges

def find_next_unignored( text, start, pattern, ignores=[]):
    """Find the next occurence of pattern starting from start, excluding all
    positions given in ignores. If none is found, it returns -1."""

    next_match = text.find( pattern, start )
    while next_match != -1:
        if next_match not in ignores: return next_match
        next_match = text.find( pattern, start + 1)
        start = next_match
    return -1

def split_with_ignores(current_text, separator, this_ignores):
    """Split the text at the separator, ignoring certain positions.
    
    Basically a "current_text.split( separator )" method with the only
    difference that it will not split at any position that is contained in
    the this_ignores array """
    loc = 0
    elements = []
    while True:
      splitat = find_next_unignored(current_text, loc, separator, this_ignores )
      if splitat < 0: break
      elements.append(current_text[loc:splitat])
      loc = splitat + 1
    elements.append(current_text[loc:])
    return elements

def introduction_range(text):
    """Find the introduction"""
    m = re.search("=+.*=+", text)
    if m: return [0, m.end()]
    else: return [0, len(text)]

def math_range(text):
    pat = re.compile("<\s*math>.*?<\s*/math\s*>" , re.DOTALL )
    return _non_nestedrange( text, pat)

def nowiki_range(text):
    pat = re.compile("<\s*nowiki>.*?<\s*/nowiki\s*>" , re.DOTALL )
    return _non_nestedrange( text, pat)

def comment_range(text):
    pat = re.compile("<!--.*?-->" , re.DOTALL )
    return _non_nestedrange( text, pat)

def _non_nestedrange(text, pattern):
    """Given a compiled regex pattern this will return a list of ranges where
    this pattern occurs."""
    return [[q.start(), q.end()] for q in re.finditer(pattern , text)]

def ignoreranges(text, ranges):
    ignores =  []
    if 'math' in ranges:
        for q in math_range( text ): ignores.extend( range( q[0], q[1] ) )
    if 'nowiki' in ranges:
        for q in nowiki_range( text ): ignores.extend( range( q[0], q[1] ) )
    if 'comment' in ranges:
        for q in comment_range( text ): ignores.extend( range( q[0], q[1] ) )
    return ignores

def get_subtext(text, myrange):
    return text[myrange[0]:myrange[1]]

def sic_comment_range(text, around=50):
    """Every text that looks like <!-- sic --> and is mostly used to denote
    unusual but correct spelling at this position."""
    ranges = []
    for r in comment_range(text):
        subtext = get_subtext(text, r)
        if subtext.find('sic') != -1:
            ranges.append( [r[0]-around, r[1]+around] )
        if subtext.find('Sic!') != -1:
            ranges.append( [r[0]-around, r[1]+around] )
    return ranges

def list_ranges(text):
    """Returns the ranges of a lists, e.g. starting with *.
    
    """
    ranges = []
    for line in text.splitlines(True):
        if \
           line.strip().startswith("*") or \
           line.strip().startswith("#") or \
           line.strip().startswith(":") or \
           line.strip().startswith(";"):
             ranges.append( [text.find(line), text.find(line) + len(line)] )
    return ranges

def regularTag_range(text, tags=['nowiki', 'math', 'pre', 'gallery', 'source', 
                                 'blockquote', 'code', 'sub', 'imagemap', 'poem', 'syntaxhighlight']):
    """Returns the ranges of a some common tags.
    
    Default are 'nowiki', 'math', 'pre', 'gallery', 'source', 'blockquote',
    'code', 'sub', 'imagemap', 'poem' but they can be specified by the tags
    argument.
    """
    ranges = []
    for tag in tags:
        pat = re.compile("<\s*%s.*?>.*?<\s*/%s\s*>" % (tag, tag) , re.DOTALL )
        ranges.extend( _non_nestedrange( text, pat) )
    return ranges

def picture_range(text):
    picture_elements = []
    pic = u"\[\[(Image|Bild|Datei|File):"
    # Iterate over all starting points of a file/image
    for q in re.finditer(pic, text):
        current_start = q.start()
        ranges = findRange( "[[", "]]", text, start=current_start)
        this_ignores = []

        # Find all nested [[ ]] elements and add the nested elements to
        # this_ignores, stop when the outer element is reached.
        for rr in ranges.ranges:
            current_text = get_subtext(text, rr)
            if(text.find(current_text)==current_start):
                break
            this_ignores.extend(range(rr[0],rr[1]))

        # Recompute the ignore range for this text
        this_ignores = [i - current_start for i in this_ignores ]

        # Add any templates within to the ignored ranges
        ranges = findRange( "{{", "}}", current_text)
        for rr in ranges.ranges: this_ignores.extend(range(rr[0],rr[1]))
        this_ignores.extend(ignoreranges(current_text, ['math', 'nowiki', 'comment']) )

        # Now split the outer element at the vertical bar ("|") but ignoring those that are within nested
        elements = split_with_ignores(current_text, "|", this_ignores)
        # remove leading and trailing brackets [[ and ]]
        if len(elements) > 0: elements[0] = elements[0][2:]
        if len(elements) > 1: elements[-1] = elements[-1][:-2]
        p = PictureText(start = current_start, fulltext = current_text, elements = elements)
        picture_elements.append(p)
    return picture_elements 

def references_range(text):
    reftagRange = []

    #TODO there is also group attribute
    #TODO capture <ref name="" group="">...</ref>.
    #capture <ref name="">...</ref>
    refName = u"<ref\s+[^>]*\s*/>"
    for q in re.finditer(refName, text, re.DOTALL):
        reftagRange.append([q.start(),q.end()])


    ref = "<ref[^>^/]*>"
    for q in re.finditer(ref, text):
        m = re.search("</ref\s*>", text[q.start():])
        if m:
            reftagRange.append([q.start(),m.end()+q.start()])
        else:
            pass

    return reftagRange

def hyperlink_range(text):
    tRange =  [];
    loc = 0
    # Find all occurences of http(s)// and then append everything except spaces
    # or newlines.
    while True:
        s = text.find('https://', loc)
        s2 = text.find('http://', loc)
        if s ==-1 and s2 == -1: break
        if not s == -1:
            if not s2 == -1:
                if s < s2: first = s
                else: first = s2
            else: first = s
        else: first = s2
        second = first
        while second < len(text) and not (text[second] == ' ' or text[second] == '\n'):
            second += 1
        tRange.append([first, second])
        loc = second
    return tRange


