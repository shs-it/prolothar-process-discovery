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
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.choice_candidates import find_choice_candidates_in_dfg
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

class TestChoiceCandidates(unittest.TestCase):

    def test_find_choice_candidates_in_dfg(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', '1')
        dfg.add_count('1', '2')
        dfg.add_count('1', '5')
        dfg.add_count('2', '4')
        dfg.add_count('2', '6')
        dfg.add_count('4', '5')

        found_choices = find_choice_candidates_in_dfg(dfg)

        expected_choices = set([
            Choice([Singleton('1'), Singleton('4')]),
            Choice([Singleton('2'), Singleton('5')]),
            Choice([Singleton('4'), Singleton('6')]),
        ])

        self.maxDiff = None
        self.assertSetEqual(expected_choices, found_choices)

if __name__ == '__main__':
    unittest.main()