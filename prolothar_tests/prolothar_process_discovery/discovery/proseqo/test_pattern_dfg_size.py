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
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton

from prolothar_process_discovery.discovery.proseqo.pattern_dfg_size.nr_of_nodes import NrOfNodes
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_size.nr_of_edges import NrOfEdges
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_size.sum_of import SumOf

class TestPatternDfgSize(unittest.TestCase):

    def setUp(self):
        self.dfg_without_patterns = PatternDfg()
        self.dfg_without_patterns.add_count('0', '1')
        self.dfg_without_patterns.add_count('0', '7')
        self.dfg_without_patterns.add_count('1', '2')
        self.dfg_without_patterns.add_count('2', '4')
        self.dfg_without_patterns.add_count('2', '6')
        self.dfg_without_patterns.add_count('4', '5')
        self.dfg_without_patterns.add_count('5', '1')
        self.dfg_without_patterns.add_count('5', '4')
        self.dfg_without_patterns.add_count('7', '8')
        self.dfg_without_patterns.add_count('8', '6')

        self.dfg_with_patterns = PatternDfg()
        self.dfg_with_patterns.add_count('0', '[1,2]')
        self.dfg_with_patterns.add_count('[1,2]', '[4,5]')
        self.dfg_with_patterns.add_count('[1,2]', '6')
        self.dfg_with_patterns.add_count('[4,5]', '[1,2]')
        self.dfg_with_patterns.add_count('[4,5]', '[4,5]')
        self.dfg_with_patterns.add_pattern('[1,2]', Sequence([Singleton('1'),
                                                              Singleton('2')]))
        self.dfg_with_patterns.add_pattern('[4,5]', Sequence([Singleton('4'),
                                                              Singleton('5')]))

    def test_nr_of_nodes(self):
        self.assertEqual(8, NrOfNodes().compute_size(self.dfg_without_patterns))
        self.assertEqual(4, NrOfNodes().compute_size(self.dfg_with_patterns))

    def test_nr_of_edges(self):
        self.assertEqual(10, NrOfEdges().compute_size(self.dfg_without_patterns))
        self.assertEqual(5, NrOfEdges().compute_size(self.dfg_with_patterns))

    def test_sum_of(self):
        sum_of = SumOf([NrOfNodes(), NrOfEdges()])
        self.assertEqual(18, sum_of.compute_size(self.dfg_without_patterns))
        self.assertEqual(9, sum_of.compute_size(self.dfg_with_patterns))

if __name__ == '__main__':
    unittest.main()