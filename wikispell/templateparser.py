#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
A template parser library that tries to emulate the mediawiki template parsing.
"""

import re
import textrange_parser

class Template:

    def __init__(self):
        self.parameters = {}
        self.parameters_order = []
        self.template_Error = False
        self.start = -1
        self.end = -1

    def init_with_text(self, boxtext, allowEmpty=False):
        """Initialize the template object with wikitext. This code assumes that
        the text argument *only* contains a template, e.g. starts with
        "{{template name" and ends with a matching "}}". Thus it is easier to
        call parse_template when dealing with a full article; parse_template
        will extract the template text and then call this method."""

        # First we find other tags that may contain special characters and then
        # we find all the inner templates. This approach will return, as a last
        # result, the outermost template which we then remove.
        ignore_mathcomm = textrange_parser.ignoreranges( boxtext, ['math', 'comment', 'nowiki'])
        inner_templates = textrange_parser.findRange( "{{", "}}", boxtext, ignore_in = ignore_mathcomm)
        assert inner_templates.ranges[-1] == [0, len( boxtext) ]
        inner_templates.remove_last_range()
        inner_links = textrange_parser.findRange( "[[", "]]", boxtext, ignore_in = ignore_mathcomm)

        # Here we determine all positions that are either within inner
        # templates, within links, within a math or nowiki-tag, a comment or
        # within a reference.
        refrange = textrange_parser.Ranges()
        refrange.ranges = textrange_parser.references_range(boxtext)
        ignores = []
        ignores.extend( inner_templates.get_large_ranges() )
        ignores.extend( inner_links.get_large_ranges() )
        ignores.extend( ignore_mathcomm )
        ignores.extend( refrange.get_large_ranges() )

        # Next we split the template text at the vertical bars, ignoring all of
        # the above special positions. 
        elements = textrange_parser.split_with_ignores(boxtext, "|", ignores)

        if allowEmpty and len(elements) == 1:
            return 

        assert len(elements) > 1
        # remove leading and trailing brackets {{  and }
        if len(elements) > 0: elements[0] = elements[0][2:]
        if len(elements) > 1: elements[-1] = elements[-1][:-2]

        # Here we go through the text split at vertical bars and store them as
        # key-value pairs in the self.parameters dictionary.
        for i,curr in enumerate(elements[1:]):
            mysplit = curr.split( '=' )
            # get rid of the trailing "|" and the beginning "="
            value = curr[ len( mysplit[0]) + 1:]
            key =  mysplit[0].strip() 
            if len( mysplit ) < 2: self.template_Error = True
            if len( mysplit ) == 1: 
                value = curr.strip()
                key = 'parameter_%s' % i
            if len(value) > 0 and value[-1] == '|': value = value[:-1]

            self.parameters[key] = value.strip()
            self.parameters_order.append(key)

    def to_wikitext(self, extra_space = '', align=False):
        """Convert the template object back to wikitext"""
        res = '{{' + self.name + '\n'
        max_len = max( [len(k) for k in self.parameters_order] )
        for k in self.parameters_order:
            v = self.parameters[k]
            if align: res += " | " + k + extra_space + " " * (max_len-len(k)) + " = " + v + "\n"
            else: res += " | " + k + " = " + v + "\n"
        res += "}}"
        return res

    def add_parameter(self, parname, before=None, after=None):
        """ Add a parameter to the template.

        You can choose the position (default is at the end).
        Set EITHER before OR after
        """
        newp = []
        if before is not None and after is not None: raise NameError, \
           "You cannot set both arguments: before AND after"
        for k in self.parameters_order:
            if before and before == k:
                newp.append(parname)
            newp.append(k)
            if after and after == k:
                newp.append(parname)
        #just append to the end
        if before is None and after is None: newp.append(parname)
        self.parameters_order = newp

    def set_parameter(self, parname, value):
        self.parameters[parname] = value

def parse_template(text, template_name=None, start=None, allowEmpty=False):
    """Parse a Wikipedia template and return a template object.

    Parses a wikipedia template of the form
        {{template_name |key1 = value1 |key2 = value2}}
    into a hash with the same key-value pairs.
    Note that it will also parse nested templates correctly.
    """

    # Lets find the startpoint of the template
    if not start is None:
        startpoint = start
    elif not template_name is None:
      match = re.search( "{{\s*%s" % template_name, text )
      startpoint = match.start()
    else:
        raise Exception('Either template name or startpoint needs to be provided.')

    #now lets find inner math and comment statements
    ignore_mathcomm = textrange_parser.ignoreranges( text, ['math', 'comment', 'nowiki'])
    ranges = textrange_parser.findRange( "{{", "}}", text,
                     start=startpoint, ignore_in = ignore_mathcomm )

    # There should be only one match that starts at startpoint which is our
    # template! Extract the markup text of the template (boxtext) and process.
    template_range = [r for r in ranges.ranges if r[0] == startpoint]
    assert len( template_range ) == 1
    template_range = template_range[0]
    boxtext = text[ template_range[0] : template_range[1]]

    template = Template()
    template.start = template_range[0]
    template.end = template_range[1]
    template.name = template_name
    template.init_with_text(boxtext, allowEmpty)

    return template

def get_all_templates(text):

    templates = []
    Rtemplate = re.compile( ur'{{(msg:)?(?P<name>[^{\|]+?)[|}]')
    for m in Rtemplate.finditer(text):
        t = parse_template(text,start=m.start())
        t.template_name = m.group('name').strip()
        templates.append(t)

    return templates



