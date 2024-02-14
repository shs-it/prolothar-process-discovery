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
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern.loop import Loop
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import find_isolated_sequences_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import find_isolated_sequence_from_candidate_node
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import return_induced_sequence_if_existing
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

class TestIsolatedSequences(unittest.TestCase):

    def test_find_isolated_sequences_in_dfg(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', '1')
        dfg.add_count('1', '2')
        dfg.add_count('2', '4')
        dfg.add_count('2', '6')
        dfg.add_count('4', '5')
        dfg.add_count('5', '1')
        dfg.add_count('6', '7')
        dfg.add_count('7', '8')
        dfg.add_count('8', '6')
        dfg.add_count('8', '9')
        dfg.add_count('9', '10')

        found_sequences = find_isolated_sequences_in_dfg(dfg)

        expected_sequences = [
            Sequence.from_activity_list(['1', '2']),
            Sequence.from_activity_list(['4', '5']),
            Sequence.from_activity_list(['6', '7']),
            Sequence.from_activity_list(['9', '10']),
        ]

        self.assertCountEqual(expected_sequences, found_sequences)

    def test_find_isolated_sequences_in_dfg_wabenhistorie_excerpt(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('SIF4', 'F4H7')
        dfg.add_count('F4H7', 'Q1R1')
        dfg.add_count('Q1R1', 'RQRM')
        dfg.add_count('SIF4', 'F4H2')
        dfg.add_count('F4H2', 'Q1O2')
        dfg.add_count('Q1O2', 'H2H4')

        found_sequences = find_isolated_sequences_in_dfg(dfg)

        expected_sequences = [
            Sequence.from_activity_list(['F4H7', 'Q1R1', 'RQRM']),
            Sequence.from_activity_list(['F4H2', 'Q1O2', 'H2H4']),
        ]

        self.assertCountEqual(expected_sequences, found_sequences)

    def test_find_isolated_sequences_in_dfg_wabenhistorie_excerpt2(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('[DIKB,BUEI,OFH1]', 'EZH1')
        dfg.add_count('EZH1', 'STH1')
        dfg.add_count('EZH1', 'USH1')
        dfg.add_count('STH1', 'USH1')

        found_sequences = find_isolated_sequences_in_dfg(dfg)

        expected_sequences = [
            Sequence.from_activity_list(['[DIKB,BUEI,OFH1]', 'EZH1']),
        ]

        self.assertCountEqual(expected_sequences, found_sequences)

    def test_find_isolated_sequence_from_candidate_node(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', '1')
        dfg.add_count('1', '2')
        dfg.add_count('2', '4')
        dfg.add_count('2', '6')
        dfg.add_count('4', '5')
        dfg.add_count('5', '1')
        dfg.add_count('6', '7')
        dfg.add_count('7', '8')
        dfg.add_count('8', '6')
        dfg.add_count('8', '9')
        dfg.add_count('9', '10')

        found_sequence = find_isolated_sequence_from_candidate_node(
                dfg, dfg.nodes['8'])
        self.assertEqual(None, found_sequence)

        found_sequence = find_isolated_sequence_from_candidate_node(
                dfg, dfg.nodes['9'])
        self.assertEqual(Sequence.from_activity_list(['9', '10']), found_sequence)

        found_sequence = find_isolated_sequence_from_candidate_node(
                dfg, dfg.nodes['10'])
        self.assertEqual(Sequence.from_activity_list(['9', '10']), found_sequence)

    def test_return_induced_sequence_if_existing(self):
        dfg = PatternDfg()
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

        induced_sequence = return_induced_sequence_if_existing(
                Loop(Singleton('0')), dfg)
        self.assertEqual(
                Loop(Singleton('0')), induced_sequence)

        induced_sequence = return_induced_sequence_if_existing(
                Loop(Sequence.from_activity_list(['4', '5'])), dfg)
        expected_induced_sequence = Sequence([
                Singleton('1'),
                Singleton('2'),
                Singleton('3'),
                Loop(Sequence.from_activity_list(['4', '5']))
        ])
        self.assertEqual(
                expected_induced_sequence, induced_sequence)

if __name__ == '__main__':
    unittest.main()