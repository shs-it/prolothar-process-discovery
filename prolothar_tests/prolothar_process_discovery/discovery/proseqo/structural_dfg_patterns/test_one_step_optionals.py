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
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_optionals import find_one_step_optionals_in_dfg
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

class TestOneStepOptionals(unittest.TestCase):

    def test_find_one_step_optionals_in_dfg(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('1', '2')
        dfg.add_count('1', '5')
        dfg.add_count('2', '5')
        dfg.add_count('2', '6')
        dfg.add_count('6', '8')
        dfg.add_count('6', '9')
        dfg.add_count('8', '9')

        found_optionals = find_one_step_optionals_in_dfg(dfg)

        expected_optionals = [
            Optional(Singleton('8'))
        ]

        self.maxDiff = None
        self.assertCountEqual(expected_optionals, found_optionals)

    def test_find_one_step_optionals_in_dfg_two_parents(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('WNEK', 'HSAN')
        dfg.add_count('WNEK', 'GREX')
        dfg.add_count('WRIC', 'HSAN')
        dfg.add_count('WRIC', 'GREX')
        dfg.add_count('HSAN', 'GREX')

        found_optionals = find_one_step_optionals_in_dfg(dfg)

        expected_optionals = [
            Optional(Singleton('HSAN'))
        ]

        self.maxDiff = None
        self.assertCountEqual(expected_optionals, found_optionals)

    def test_find_one_step_optionals_in_dfg_without_optional(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('NBST', 'PPST')

        found_optionals = find_one_step_optionals_in_dfg(dfg)

        expected_optionals = []

        self.maxDiff = None
        self.assertCountEqual(expected_optionals, found_optionals)

    def test_find_one_step_optionals_in_dfg_with_parent_with_many_connections(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('KRM1', 'NBEB')
        dfg.add_count('RIKO', 'NBEB')
        dfg.add_count('NBEB', 'OEEO')
        dfg.add_count('NBEB', 'KRWP')
        #optional part
        dfg.add_count('NBEB', 'VWF4')
        dfg.add_count('VWF4', 'KRWR')
        dfg.add_count('NBEB', 'KRWR')

        found_optionals = find_one_step_optionals_in_dfg(dfg)

        expected_optionals = [Optional(Singleton('VWF4'))]

        self.maxDiff = None
        self.assertCountEqual(expected_optionals, found_optionals)

    def test_find_one_step_optionals_in_dfg_with_cycle(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('OFH2', 'EZH2')
        dfg.add_count('OFH2', 'STH2')
        dfg.add_count('EZH2', 'STH2')
        dfg.add_count('STH2', 'OFH2')

        found_optionals = find_one_step_optionals_in_dfg(dfg)

        expected_optionals = [Optional(Singleton('EZH2'))]

        self.maxDiff = None
        self.assertCountEqual(expected_optionals, found_optionals)

    def test_find_one_step_optionals_in_dfg_with_multiple_predecessors_and_ancestors(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('A1', 'B')
        dfg.add_count('A1', 'D')
        dfg.add_count('A1', 'C1')
        dfg.add_count('A1', 'C2')
        dfg.add_count('A2', 'B')
        dfg.add_count('A2', 'C1')
        dfg.add_count('A2', 'C2')
        dfg.add_count('A2', 'E')
        dfg.add_count('B', 'C1')
        dfg.add_count('B', 'C2')
        dfg.add_count('C1', 'D')

        found_optionals = find_one_step_optionals_in_dfg(dfg)
        expected_optionals = [Optional(Singleton('B'))]
        self.assertCountEqual(expected_optionals, found_optionals)

    def test_find_one_step_optionals_in_dfg_find_induced_sequences_no_sequence(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('OFH2', 'EZH2')
        dfg.add_count('OFH2', 'STH2')
        dfg.add_count('EZH2', 'STH2')
        dfg.add_count('STH2', 'OFH2')

        found_optionals = find_one_step_optionals_in_dfg(dfg, find_induced_sequences=True)

        expected_optionals = [Optional(Singleton('EZH2'))]

        self.maxDiff = None
        self.assertCountEqual(expected_optionals, found_optionals)

    def test_find_one_step_optionals_in_dfg_find_induced_sequences_with_sequence(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('1', '2')
        dfg.add_count('1', '5')
        dfg.add_count('2', '5')
        dfg.add_count('2', '6')
        dfg.add_count('6', '8')
        dfg.add_count('6', '9')
        dfg.add_count('8', '9')

        found_optionals = find_one_step_optionals_in_dfg(dfg, find_induced_sequences=True)

        expected_optionals = [Sequence([Singleton('6'),
                                        Optional(Singleton('8')),
                                        Singleton('9')])]

        self.maxDiff = None
        self.assertCountEqual(expected_optionals, found_optionals)

    def test_find_one_step_optionals_in_dfg_with_selfloop(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', '0')
        dfg.add_count('0', '1')
        dfg.add_count('1', '2')
        dfg.add_count('2', '3')
        dfg.add_count('3', '4')
        dfg.add_count('4', '5')
        dfg.add_count('5', '4')
        dfg.add_count('0', '7')
        dfg.add_count('7', '8')
        dfg.add_count('8', '6')

        found_optionals = find_one_step_optionals_in_dfg(dfg)

        expected_optionals = []

        self.maxDiff = None
        self.assertCountEqual(expected_optionals, found_optionals)

    def test_find_one_step_optionals_with_choice(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('A', 'B')
        dfg.add_count('A', 'C')
        dfg.add_count('A', 'D')
        dfg.add_count('B', 'D')
        dfg.add_count('C', 'D')

        self.assertCountEqual(
                [Optional(Singleton('B')), Optional(Singleton('C'))],
                find_one_step_optionals_in_dfg(dfg))

if __name__ == '__main__':
    unittest.main()