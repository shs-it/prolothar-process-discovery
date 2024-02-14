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
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.sequence_candidates import find_sequence_candidates_in_dfg
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

class TestSequenceCandidates(unittest.TestCase):

    def test_find_sequence_candidates_in_dfg(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', '1')
        dfg.add_count('1', '2')
        dfg.add_count('1', '5')
        dfg.add_count('2', '4')
        dfg.add_count('2', '6')
        dfg.add_count('4', '5')

        found_patterns = find_sequence_candidates_in_dfg(dfg)

        expected_patterns = set([
            Sequence.from_activity_list(['0', '1']),
            Sequence.from_activity_list(['0', '1', '2']),
            Sequence.from_activity_list(['1', '2']),
            Sequence.from_activity_list(['2', '4']),
            Sequence.from_activity_list(['2', '6']),
            Sequence.from_activity_list(['4', '5']),
        ])

        self.maxDiff = None
        self.assertSetEqual(expected_patterns, found_patterns)

    def test_find_sequence_candidates_in_dfg_with_self_loop(self):
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

        expected_patterns = set()
        for expected_sequence in [
                [1,2],
                [1,2,3],
                [7,8,6],
                [8,6],
                [1,2,3,4,5],
                [2,3],
                [7,8]]:
            expected_patterns.add(Sequence.from_activity_list(
                    [str(a) for a in expected_sequence]))

        found_patterns = find_sequence_candidates_in_dfg(dfg)
        self.maxDiff = None
        self.assertSetEqual(expected_patterns, found_patterns)

    def test_find_sequence_candidates_in_dfg_with_multiple_weak_edges(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', '0', count=1)
        dfg.add_count('0', '1', count=100)
        dfg.add_count('0', '2', count=1)
        dfg.add_count('1', '0', count=1)
        dfg.add_count('1', '2', count=100)
        dfg.add_count('2', '0', count=1)

        expected_patterns = set()

        expected_patterns.add(
                Sequence.from_activity_list(['0', '1']),
        )
        expected_patterns.add(
                Sequence.from_activity_list(['1', '2']),
        )
        found_patterns = find_sequence_candidates_in_dfg(dfg)

        self.maxDiff = None
        self.assertSetEqual(expected_patterns, found_patterns)

if __name__ == '__main__':
    unittest.main()