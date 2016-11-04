#!/usr/bin/python
# -*- coding: utf-8  -*-

"""Unit test for textrange_parser
"""
#
# Distributed under the terms of the MIT license.
#

import unittest
import test_utils

import testSamples
from wikispell.textrange_parser import *

class TextrangeeParserTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_alternative_break(self):
        sample = testSamples.test_sample2
        albr = ['</ref>', '\n'];
        test_result = findRange('\'\'\'', '\'\'\'', sample,alternativeBreak=albr)
        self.assertEqual(len(test_result.ranges), 5)
        expected = [[148, 157], [237, 288], [374, 385], [606, 621], [912, 959]]
        self.assertEqual(test_result.ranges[0], expected[0] )
        self.assertEqual(test_result.ranges[1], expected[1] )
        self.assertEqual(test_result.ranges[2], expected[2] )
        self.assertEqual(test_result.ranges[3], expected[3] )
        self.assertEqual(test_result.ranges[4], expected[4] )
        self.assertEqual(test_result.ranges, expected )

    def test_find_range_test3(self):
        #here we have three levels of nesting
        sample = testSamples.N_Chlorsuccinimid_rev80386547
        expected = [[727, 739], [707, 764], [1078, 1099], [1131,
                                    1149], [1181, 1207], [39, 1242]]
        ignores = []
        for q in math_range( sample ): ignores.extend( range( q[0], q[1] ) )
        ranges = findRange( "{{", "}}", sample,
                         start=39, ignore_in = ignores )
        self.assertEqual(ranges.ranges, expected)

    def test_find_range_test2(self):
        #here we have some math within the infobox
        sample = testSamples.Aluminiumnitrat_rev69770393
        expected = [[798, 870], [1168, 1192], [1217, 1236],
                          [1261, 1281], [0, 1309]]
        ignores = []
        for q in math_range( sample ): ignores.extend( range( q[0], q[1] ) )
        ranges = findRange( "{{", "}}", sample,
                         start=0, ignore_in = ignores )
        self.assertEqual(ranges.ranges, expected)

    def test_find_range_test1(self):
        #test with ignoring math
        sample = testSamples.Kaliumpermanganat_rev73384760
        expected = [[345, 361], [363, 379], [583, 654], [1015, 1031],
                          [1057, 1083], [1109, 1131], [1157, 1178], [0, 1248]]
        ignores = []
        for q in math_range( sample ): ignores.extend( range( q[0], q[1] ) )
        ranges = findRange( "{{", "}}", sample,
                         start=0, ignore_in = ignores )
        self.assertEqual(ranges.ranges, expected)

    def test_find_range_test0(self):
        #test without any ignoring, only ranges per se
        sample = testSamples.Kaliumpermanganat_rev73384760
        expected = [[345, 361], [363, 379], [583, 654], [1015, 1031],
                          [1057, 1083], [1109, 1131], [1157, 1178], [0, 1248],
                          ]
        ignores = []
        ranges = findRange( "{{", "}}", sample,
                         start=0, ignore_in = ignores )
        self.assertEqual(ranges.ranges, expected)

    def test_find_range_unmatched_opening(self):
        sample = """{{Lorem ipsum dolor }} sit amet, {{ consectetur {{adipisicing elit, {{sed do eiusmod}} tempor incididunt ut laboreet dolore  """
        ranges = findRange( "{{", "}}", sample, start=0)
        self.assertFalse(ranges.match)
        self.assertEqual(len(ranges.not_matching), 2)
        self.assertEqual(ranges.not_matching, [33, 48])

    def test_find_range_unmatched_closing(self):
        sample = """{{Lorem ipsum dolor }} sit amet, }} consectetur {{adipisicing elit, }}sed do eiusmod}} tempor incididunt ut laboreet dolore  """
        ranges = findRange( "{{", "}}", sample, start=0)
        self.assertFalse(ranges.match)
        self.assertEqual(len(ranges.not_matching), 2)
        self.assertEqual(ranges.not_matching, [33, 84])

    def test_find_next_unignored(self):
        sample = testSamples.test_sample1
        ignores = []
        for q in math_range( sample ): ignores.extend( range( q[0], q[1] ) )
        self.assertEqual(283, find_next_unignored( sample, 0, '}}', ignores))

    def test_math_range(self):
        sample = testSamples.test_sample1
        expected = [[122, 160], [200, 248]]
        computed = math_range(sample)
        self.assertEqual(expected, computed  )

    def test_introduction_range(self):
        sample = testSamples.test_sample1
        expected = [0, 317]
        self.assertEqual(expected, introduction_range(sample) )

    def test_sic_comment_range(self):
        sample = testSamples.test_sample1
        expected = [[373, 486]]
        computed = sic_comment_range(sample)
        self.assertEqual(expected, computed )

    def test_regular_tag_range(self):
        sample = testSamples.test_sample1
        expected = [[122, 160], [200, 248]]
        computed = regularTag_range(sample)
        self.assertEqual(expected, computed)

    def test_list_ranges(self):
        sample = testSamples.test_sample1
        expected = [ [629, 686] ]
        computed = list_ranges(sample)
        self.assertEqual(expected, computed)

        text = u"""
        Here is some other text
         ; which is in 
         ; a list
        and then not
          ## but then again
          *and again
        but finally not
         : and some indent
        """

        expected = [[33, 57], [57, 75], [96, 124], [124, 145], [169, 196]]
        computed = list_ranges(text)
        self.assertEqual(expected, computed)

    def test_picture_range(self):
        sample = testSamples.test_sample1
        expected = [[122, 160], [200, 248]]
        computed = picture_range(sample) 
        self.assertEqual(2, len(computed) )
        self.assertEqual(computed[0].fulltext, u"[[Datei:Al3+.svg|40px|Aluminiumion]]" )
        self.assertEqual(computed[0].elements[-1], "Aluminiumion")
        self.assertEqual(computed[0].start, 85)
        self.assertEqual(computed[1].fulltext, u"[[Datei:Nitrat-Ion.svg|70px|Nitration]]" )
        self.assertEqual(computed[1].start, 161)
        self.assertEqual(computed[1].elements[-1], "Nitration")

    def test_picture_range_complicated(self):

        text = u"""
        Here is some other text
        [[Datei:Al3+.svg|40px|Aluminiumion with some [[other text|linked to]] and then [[this]]]] <math>\mathrm{ \
                \Biggl[}</math> [[and here some more ]] and more text again [[Datei:Nitrat-Ion.svg|70px|Nitration]]<math>\mathrm{ \
                \!\ \Biggr]_3^{-}}</math>
        """
        computed = picture_range(text) 

        self.assertEqual(2, len(computed) )
        self.assertEqual(computed[0].fulltext, "[[Datei:Al3+.svg|40px|Aluminiumion with some [[other text|linked to]] and then [[this]]]]" )
        self.assertEqual(len(computed[0].elements), 3)
        self.assertEqual(computed[0].elements[-1], "Aluminiumion with some [[other text|linked to]] and then [[this]]")
        self.assertEqual(computed[0].start, 41)
        self.assertEqual(computed[1].fulltext, "[[Datei:Nitrat-Ion.svg|70px|Nitration]]" )
        self.assertEqual(len(computed[1].elements), 3)
        self.assertEqual(computed[1].start, 222)

    def test_picture_range_complicated_2(self):
        # The goal here is to extract the image with its elements completely
        # without being distracted by intermediate bars in the caption.
        text = """ Here is some other text 
        [[Datei:Nitrat-Ion.svg|70px|Nitration]] and second file 
        [[File:Aedes aegypti bloodfeeding CDC Gathany.jpg|thumb|''[[Aedes aegypti]]'' 
         feeding <!-- some comment here || doing bad stuff --> and {{cite web |url=www.example.com |title= myTitle |author=
         myAuthor |date= |work= |publisher= |accessdate=22 January 2012}} ]] """
        computed = picture_range(text) 
        self.assertEqual(computed[0].fulltext, "[[Datei:Nitrat-Ion.svg|70px|Nitration]]" )
        self.assertEqual(len(computed[0].elements), 3)
        self.assertEqual(computed[0].start, 34)

        self.assertEqual(len(computed[1].elements), 3)
        self.assertEqual(computed[1].start, 99)
        self.assertEqual(computed[1].fulltext[:77], "[[File:Aedes aegypti bloodfeeding CDC Gathany.jpg|thumb|''[[Aedes aegypti]]''" )
        self.assertEqual(computed[1].elements[0], "File:Aedes aegypti bloodfeeding CDC Gathany.jpg" )
        self.assertEqual(computed[1].elements[1], "thumb" )
        self.assertEqual(computed[1].elements[2][-50:], " |work= |publisher= |accessdate=22 January 2012}} " )

    def test_hyperlink_range(self):
        sample = testSamples.test_sample1
        expected =  [[576, 600], [632, 657]]
        computed = hyperlink_range(sample)
        self.assertEqual(2, len(computed) )
        self.assertEqual(expected, computed )

    def test_split_with_ignores(self):
        text = '{{template_name |key1 = value1 |key2 = value2}} '
        result = split_with_ignores(text, '|', [])
        self.assertEqual(len(result), 3 )
        self.assertEqual(result[0], '{{template_name ' )
        self.assertEqual(result[1], 'key1 = value1 ' )
        self.assertEqual(result[2], 'key2 = value2}} ' )
        text = '{{template_name |key1 = value1 |key2 = value2}}'
        result = split_with_ignores(text, '|', [])
        self.assertEqual(len(result), 3 )
        self.assertEqual(result[0], '{{template_name ' )
        self.assertEqual(result[1], 'key1 = value1 ' )
        self.assertEqual(result[2], 'key2 = value2}}' )
        text = '{{template_name |key1 = value1 |key2 = value2}}'
        result = split_with_ignores(text, '|', [16])
        self.assertEqual(len(result), 2 )
        self.assertEqual(result[0], '{{template_name |key1 = value1 ' )
        self.assertEqual(result[1], 'key2 = value2}}' )

    def test_references_range(self):
        text = """
        Lorem ipsum
        <ref name=roempp/>
        Lorem ipsum
        <ref name="roempp"/>
        Lorem ipsum
        sorte.<ref name=schil>[http://www.oesterreichwein.at Beschreibung der Rebsorte].</ref> Er wird als [[Roséwein]
        [[Roséwein]]<ref name=schil/><ref>[http://www.ris.bka.gv.at Weinbezeichnungsverordnung], Teil II Nr. 111/2011: § 1 </ref>
        Lorem ipsum
        """
        sample = text
        expected = [[29, 47], [76, 96], [258, 275], [131, 211], [275, 368]]
        computed = references_range(sample) 
        self.assertEqual(expected, computed)

        sample = testSamples.test_sample2
        expected = [[787, 959]]
        computed = references_range(sample) 
        self.assertEqual(expected, computed)

        sample = testSamples.test_sample2
        expected = [[787, 959]]
        computed = references_range(sample) 
        self.assertEqual(expected, computed)

        sample = testSamples.Kaliumpermanganat_rev73384760
        expected = [[459, 479], [708, 728], [767, 787], [876, 896], [969, 989], [1225, 1245], [564, 660]]
        computed = references_range(sample) 
        self.assertEqual(sorted(expected), sorted(computed) )

        sample = testSamples.Aluminiumnitrat_rev69770393
        expected = [[1025, 1050], [1075, 1093], [1118, 1143], [1928, 1953], [2078, 2096], [2484, 2509], [2945, 2970], [435, 555], [774, 876], [1582, 1632]]
        computed = references_range(sample) 
        self.assertEqual(sorted(expected), sorted(computed) )


if __name__ == "__main__":
    unittest.main()
