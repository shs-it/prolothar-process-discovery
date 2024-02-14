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
from prolothar_process_discovery.discovery.proseqo.pattern.parallel import Parallel
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_common.models.data_petri_net import DataPetriNet

class TestParallel(unittest.TestCase):

    def test_remove_activity_and_without_degeneration(self):
        parallel = Parallel([Sequence.from_activity_list(['A', 'B']),
                             Singleton('C')])

        parallel.remove_activity('A')
        self.assertEqual(2, parallel.get_nr_of_subpatterns())

        self.assertFalse(parallel.branches[1].is_singleton())
        parallel = parallel.without_degeneration()[0]
        self.assertTrue(parallel.branches[1].is_singleton())

        parallel.remove_activity('B')

        try:
            parallel.remove_activity('C')
            self.assertFail('should lead to ValueError')
        except ValueError:
            pass

        self.assertTrue(parallel.without_degeneration()[0].is_singleton())

    def test_fold_and_expand_dfg(self):
        dfg = PatternDfg()
        dfg.add_count('0', 'A', count=1)
        dfg.add_count('0', 'B', count=2)
        dfg.add_count('0', 'C', count=3)
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'A')
        dfg.add_count('B', 'C')
        dfg.add_count('C', 'A')
        dfg.add_count('A', '1', count=7)
        dfg.add_count('C', '1', count=4)

        folded_dfg = dfg.fold([Parallel.from_activity_list(['A','B','C'])])

        expected_folded_dfg = PatternDfg()
        expected_folded_dfg.add_count('0', '(A||B||C)', count=6)
        expected_folded_dfg.add_count('(A||B||C)', '1', count=11)

        self.assertEqual(expected_folded_dfg, folded_dfg)

        expected_expanded_dfg = PatternDfg()
        expected_expanded_dfg.add_count('0', 'A', count=0)
        expected_expanded_dfg.add_count('0', 'B', count=0)
        expected_expanded_dfg.add_count('0', 'C', count=0)
        expected_expanded_dfg.add_count('A', 'B', count=0)
        expected_expanded_dfg.add_count('A', 'C', count=0)
        expected_expanded_dfg.add_count('B', 'A', count=0)
        expected_expanded_dfg.add_count('B', 'C', count=0)
        expected_expanded_dfg.add_count('C', 'A', count=0)
        expected_expanded_dfg.add_count('C', 'B', count=0)
        expected_expanded_dfg.add_count('A', '1', count=0)
        expected_expanded_dfg.add_count('B', '1', count=0)
        expected_expanded_dfg.add_count('C', '1', count=0)

        expanded_dfg = folded_dfg.expand()
        self.assertEqual(expected_expanded_dfg, expanded_dfg)

    def test_fold_and_expand_dfg_nested(self):
        pattern = Parallel([
                Sequence.from_activity_list(['A', 'B']),
                Sequence.from_activity_list(['C', 'D'])
        ])
        dfg = PatternDfg()
        dfg.add_node(pattern.get_activity_name())
        dfg.add_pattern(pattern.get_activity_name(), pattern)

        actual_expanded_dfg = dfg.expand()

        expected_expanded_dfg = PatternDfg()
        expected_expanded_dfg.add_count('A', 'B')
        expected_expanded_dfg.add_count('A', 'C')
        expected_expanded_dfg.add_count('A', 'D')
        expected_expanded_dfg.add_count('B', 'C')
        expected_expanded_dfg.add_count('B', 'D')
        expected_expanded_dfg.add_count('C', 'D')
        expected_expanded_dfg.add_count('C', 'A')
        expected_expanded_dfg.add_count('C', 'B')
        expected_expanded_dfg.add_count('D', 'A')
        expected_expanded_dfg.add_count('D', 'B')
        for edge in expected_expanded_dfg.get_edges():
            edge.count = 0

        self.assertEqual(expected_expanded_dfg, actual_expanded_dfg)

    def test_expand_parallel_nested_in_choise(self):
        pattern = Choice([
            Parallel([
                Singleton('a'),
                Singleton('b'),
                Singleton('c')
            ]),
            Singleton('d')
        ])
        pattern_dfg = PatternDfg.of_pattern(pattern)
        pattern_dfg.add_count(pattern.get_activity_name(), pattern.get_activity_name())

        expanded_dfg = pattern_dfg.expand()
        self.assertEqual(4, expanded_dfg.get_nr_of_nodes())

    def test_add_to_petri_net(self):
        petri_net = DataPetriNet()

        parallel = Parallel([Sequence.from_activity_list(['A', 'B']),
                             Singleton('C')])

        parallel.add_to_petri_net(petri_net)
        petri_net.prune()

        self.assertEqual(5, len(petri_net.transitions))
        self.assertEqual(7, len(petri_net.places))

if __name__ == '__main__':
    unittest.main()