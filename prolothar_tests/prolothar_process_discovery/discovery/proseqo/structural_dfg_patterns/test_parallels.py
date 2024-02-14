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
from prolothar_process_discovery.discovery.proseqo.pattern.parallel import Parallel
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.parallels import find_parallel_candidates_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.parallels import find_parallel_subgraphs
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.parallels import find_parallel_subgraphs2
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.parallels import find_perfect_matching_parallels_in_dfg
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

class TestParallels(unittest.TestCase):

    def test_find_parallel_candidates_in_dfg_singletons(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', 'A')
        dfg.add_count('0', 'B')
        dfg.add_count('0', 'C')
        dfg.add_count('A', 'B')
        dfg.add_count('A', 'C')
        dfg.add_count('B', 'A')
        dfg.add_count('B', 'C')
        dfg.add_count('C', 'A')
        dfg.add_count('A', '1')
        dfg.add_count('C', '1')

        found_parallels = find_parallel_candidates_in_dfg(dfg)

        expected_parallels = [
            Parallel.from_activity_list(['A','B','C'])
        ]

        self.assertCountEqual(expected_parallels, found_parallels)

    def test_find_parallel_candidates_in_dfg_parallel_sequences(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', 'A')
        dfg.add_count('0', 'D')
        dfg.add_count('A', 'B')
        dfg.add_count('A', 'D')
        dfg.add_count('A', 'E')
        dfg.add_count('B', 'C')
        dfg.add_count('B', 'D')
        dfg.add_count('B', 'E')
        dfg.add_count('C', '1')
        dfg.add_count('C', 'E')
        dfg.add_count('D', 'E')
        dfg.add_count('D', 'A')
        dfg.add_count('D', 'B')
        dfg.add_count('E', 'C')
        dfg.add_count('E', '1')

        found_parallels = find_parallel_candidates_in_dfg(dfg)

        expected_parallels = [
            Parallel.from_activity_list(['A', 'B', 'D']),
            Parallel.from_activity_list(['C', 'E'])
        ]

        self.assertCountEqual(expected_parallels, found_parallels)

    def test_find_parallel_subgraphs(self):
        subgraph1 = PatternDfg()
        subgraph1.add_count('S1', 'A')
        subgraph1.add_count('A', 'B')
        subgraph1.add_count('A', 'C')
        subgraph1.add_count('C', 'A')
        subgraph1.add_count('B', 'A')
        subgraph1.add_count('A', 'E1')

        subgraph2 = PatternDfg()
        subgraph2.add_count('D', 'E')
        subgraph2.add_count('E', 'F')

        pattern = Parallel([SubGraph(subgraph1, [], []), SubGraph(subgraph2, [], [])])

        pattern_dfg = PatternDfg()
        pattern_dfg.add_count('START', pattern.get_activity_name())
        pattern_dfg.add_count(pattern.get_activity_name(), 'END')
        pattern_dfg.add_pattern(pattern.get_activity_name(), pattern)

        log = pattern_dfg.generate_log(100, random_seed=42)

        dfg = DirectlyFollowsGraph.create_from_event_log(log)

        found_patterns = find_parallel_subgraphs(dfg, log)
        self.assertTrue(found_patterns is not None)
        self.assertEqual([pattern], found_patterns)

    def test_find_perfect_matching_parallels_in_dfg(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', 'A')
        dfg.add_count('0', 'B')
        dfg.add_count('0', 'C')
        dfg.add_count('A', 'B')
        dfg.add_count('A', 'C')
        dfg.add_count('B', 'A')
        dfg.add_count('B', 'C')
        dfg.add_count('C', 'A')
        dfg.add_count('A', '1')
        dfg.add_count('B', '1')
        dfg.add_count('C', '1')

        self.assertCountEqual([], find_perfect_matching_parallels_in_dfg(dfg))
        dfg.add_count('C', 'B')
        self.assertCountEqual(
                [Parallel.from_activity_list(['A','B','C'])],
                find_perfect_matching_parallels_in_dfg(dfg))

    def test_find_parallel_subgraphs2(self):
        subgraph1 = PatternDfg()
        subgraph1.add_count('S1', 'A')
        subgraph1.add_count('A', 'B')
        subgraph1.add_count('A', 'C')
        subgraph1.add_count('C', 'A')
        subgraph1.add_count('B', 'A')
        subgraph1.add_count('A', 'E1')

        subgraph2 = PatternDfg()
        subgraph2.add_count('D', 'E')
        subgraph2.add_count('E', 'F')

        pattern = Parallel([SubGraph(subgraph1, [], []), SubGraph(subgraph2, [], [])])

        pattern_dfg = PatternDfg()
        pattern_dfg.add_count('START', pattern.get_activity_name())
        pattern_dfg.add_count(pattern.get_activity_name(), 'END')
        pattern_dfg.add_pattern(pattern.get_activity_name(), pattern)

        log = pattern_dfg.generate_log(100, random_seed=42)

        found_patterns = find_parallel_subgraphs2(log)
        self.assertTrue(found_patterns is not None)
        self.assertEqual([pattern], found_patterns)


if __name__ == '__main__':
    unittest.main()