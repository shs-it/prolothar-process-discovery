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
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.two_part_loop_candidates import find_two_part_loop_candidates_in_dfg
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

class TestTwoPartLoopCandidates(unittest.TestCase):

    def test_find_two_part_loop_candidates_in_dfg(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('A', 'B')
        dfg.add_count('A', 'A')
        dfg.add_count('B', 'A')

        found = find_two_part_loop_candidates_in_dfg(dfg)

        expected = [
            Loop(Sequence([Singleton('A'), Optional(Singleton('B'))]))
        ]

        self.assertCountEqual(expected, found)

    def test_find_two_part_loop_candidates_in_dfg_2(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('A', 'B')
        dfg.add_count('A', 'A')
        dfg.add_count('A', 'C')
        dfg.add_count('B', 'A')
        dfg.add_count('B', 'C')

        found = find_two_part_loop_candidates_in_dfg(dfg)

        expected = [
            Loop(Sequence([Singleton('A'), Optional(Singleton('B'))]))
        ]

        self.assertCountEqual(expected, found)

if __name__ == '__main__':
    unittest.main()