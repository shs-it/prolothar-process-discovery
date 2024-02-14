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
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_loops import find_isolated_loops_in_dfg
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

class TestShortIsolatedLoop(unittest.TestCase):

    def test_find_isolated_loops_in_dfg_length_2(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', 'A')
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'A')
        dfg.add_count('B', 'Z')

        found = find_isolated_loops_in_dfg(dfg)

        expected = [
            Loop(Sequence.from_activity_list(['A', 'B']))
        ]

        self.assertCountEqual(expected, found)

    def test_find_isolated_loops_in_dfg_length_3(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', 'A')
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'C')
        dfg.add_count('C', 'A')
        dfg.add_count('C', 'Z')

        found = find_isolated_loops_in_dfg(dfg)

        expected = [
            Loop(Sequence.from_activity_list(['A', 'B', 'C']))
        ]

        self.assertCountEqual(expected, found)

    def test_find_isolated_loops_in_dfg_disturbing_edge(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', 'A')
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'C')
        dfg.add_count('C', 'A')
        dfg.add_count('C', 'Z')
        dfg.add_count('1', 'B')

        found = find_isolated_loops_in_dfg(dfg)

        expected = []

        self.assertCountEqual(expected, found)

    def test_find_self_loops_in_dfg(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'B')
        dfg.add_count('B', 'C')

        found_loops = find_isolated_loops_in_dfg(dfg)

        expected_loops = [
            Loop(Singleton('B'))
        ]

        self.assertCountEqual(expected_loops, found_loops)

    def test_find_self_loop_in_graph_with_to_unconnected_nodes(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('A', 'A')
        dfg.add_node('B')

        found_loops = find_isolated_loops_in_dfg(dfg)

        expected_loops = [
            Loop(Singleton('A'))
        ]

        self.assertCountEqual(expected_loops, found_loops)

    def test_find_isolated_loops_in_dfg_induced_sequences(self):
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

        expected_loops = [
            Loop(Singleton('0')),
            Sequence([
                Singleton('1'),
                Singleton('2'),
                Singleton('3'),
                Loop(Sequence.from_activity_list(['4', '5'])),
            ])
        ]

        found_loops = find_isolated_loops_in_dfg(
                dfg, find_induced_sequences=True)

        self.assertCountEqual(expected_loops, found_loops)

if __name__ == '__main__':
    unittest.main()