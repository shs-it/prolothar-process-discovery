'''
    This file is part of Prolothar-Process-Discovery (More Info: https://github.com/shs-it/prolothar-process-discovery).

    Prolothar-Process-Discovery is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Prolothar-Process-Discovery is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Prolothar-Process-Discovery. If not, see <https://www.gnu.org/licenses/>.
'''

import unittest

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.pattern.inclusive_choice import InclusiveChoice

class TestInclusiveChoice(unittest.TestCase):

    def test_fold_dfg(self):
        dfg = PatternDfg()

        #non-blob
        dfg.add_count('a', 'b')
        dfg.add_count('b', 'c')
        dfg.add_count('c', 'd')
        dfg.add_count('d', 'e')
        dfg.add_count('e', 'f')

        #blob
        dfg.add_count('l', 'h')
        dfg.add_count('l', 'k')
        dfg.add_count('h', 'k')
        dfg.add_count('h', 'l')
        dfg.add_count('h', 'g')
        dfg.add_count('k', 'g')
        dfg.add_count('k', 'l')
        dfg.add_count('k', 'h')
        dfg.add_count('g', 'l')
        dfg.add_count('g', 'h')

        #blob to non-blob
        dfg.add_count('k', 'e')
        dfg.add_count('l', 'e')
        dfg.add_count('h', 'e', count=7)

        #non-blob to blob
        dfg.add_count('c', 'k')
        dfg.add_count('c', 'g', count=3)
        dfg.add_count('c', 'h')

        dfg_with_choice = dfg.fold([
            InclusiveChoice([
                    Singleton('g'),
                    Singleton('h'),
                    Singleton('k'),
                    Singleton('l')
            ])
        ])

        expected_dfg = PatternDfg()
        expected_dfg.add_count('a', 'b')
        expected_dfg.add_count('b', 'c')
        expected_dfg.add_count('c', 'd')
        expected_dfg.add_count('d', 'e')
        expected_dfg.add_count('e', 'f')
        expected_dfg.add_count('(g,h,k,l)', 'e', count=9)
        expected_dfg.add_count('c', '(g,h,k,l)', count=5)

        self.assertEqual(
                expected_dfg.plot(view=False, show_counts=True),
                dfg_with_choice.plot(view=False, show_counts=True))

    def test_expand_dfg(self):
        folded_dfg = PatternDfg()
        folded_dfg.add_count('c', 'd')
        folded_dfg.add_count('d', 'e')
        folded_dfg.add_count('(g,h,k)', 'e')
        folded_dfg.add_count('c', '(g,h,k)')
        folded_dfg.add_pattern('(g,h,k)', InclusiveChoice([
                    Singleton('g'),
                    Singleton('h'),
                    Singleton('k'),
            ]))

        expanded_dfg = folded_dfg.expand()

        dfg = PatternDfg()
        dfg.add_count('c', 'd')
        dfg.add_count('d', 'e')
        dfg.add_count('k', 'e')
        dfg.add_count('h', 'e')
        dfg.add_count('g', 'e')
        dfg.add_count('k', 'h')
        dfg.add_count('k', 'g')
        dfg.add_count('h', 'k')
        dfg.add_count('h', 'g')
        dfg.add_count('g', 'k')
        dfg.add_count('g', 'h')
        dfg.add_count('c', 'k')
        dfg.add_count('c', 'g')
        dfg.add_count('c', 'h')
        for edge in dfg.get_edges():
            edge.count = 0

        self.assertEqual(expanded_dfg, dfg)

if __name__ == '__main__':
    unittest.main()