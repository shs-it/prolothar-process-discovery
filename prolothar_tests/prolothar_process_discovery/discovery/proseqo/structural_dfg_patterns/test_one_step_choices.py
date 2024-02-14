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
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_choices import find_one_step_choices_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_choices import find_one_step_choice_from_branch_candidate_node
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

class TestOneStepChoices(unittest.TestCase):

    def test_find_one_step_choices_in_dfg(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', '1')
        dfg.add_count('1', '2')
        dfg.add_count('1', '5')
        dfg.add_count('2', '4')
        dfg.add_count('2', '6')
        dfg.add_count('4', '5')
        dfg.add_count('5', '12')
        dfg.add_count('5', '13')
        dfg.add_count('6', '7')
        dfg.add_count('6', '8')
        dfg.add_count('8', '11')
        dfg.add_count('8', '9')
        dfg.add_count('12', '14')
        dfg.add_count('13', '14')

        found_choices = find_one_step_choices_in_dfg(dfg)

        expected_choices = [
            Choice([Singleton('11'), Singleton('9')]),
            Choice([Singleton('12'), Singleton('13')])
        ]

        self.maxDiff = None
        self.assertCountEqual(expected_choices, found_choices)

    def test_find_one_step_choices_in_dfg_parent_with_many_connections(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('A1', 'root')
        dfg.add_count('A1', 'A2')
        dfg.add_count('A2', 'root')
        dfg.add_count('root', 'B1')
        dfg.add_count('root', 'option1')
        dfg.add_count('root', 'option2')
        dfg.add_count('option1', 'end')
        dfg.add_count('option2', 'end')

        found_choices = find_one_step_choices_in_dfg(dfg)

        expected_choices = [
            Choice([Singleton('option1'), Singleton('option2')])
        ]

        self.maxDiff = None
        self.assertCountEqual(expected_choices, found_choices)

    def test_find_one_step_choices_with_three_branches(self):
        dfg = PatternDfg()
        dfg.add_count('root', 'A')
        dfg.add_count('root', 'B')
        dfg.add_count('root', 'C')

        dfg.add_count('root2', 'D')
        dfg.add_count('root2', 'E')
        dfg.add_count('root2', 'F')
        dfg.add_count('E', 'D')

        found_choices = find_one_step_choices_in_dfg(dfg)

        expected_choices = [
            Choice([Singleton('A'), Singleton('B'), Singleton('C')])
        ]

        self.maxDiff = None
        self.assertCountEqual(expected_choices, found_choices)

    def test_choice_without_root(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('A', 'C')
        dfg.add_count('B', 'C')

        found_choices = find_one_step_choices_in_dfg(dfg)

        expected_choices = [Choice([Singleton('A'), Singleton('B')])]

        self.maxDiff = None
        self.assertCountEqual(expected_choices, found_choices)

    def test_find_one_step_choices_with_double_linked_target(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('A', 'B1')
        dfg.add_count('A', 'B2')
        dfg.add_count('B1', 'C')
        dfg.add_count('B2', 'C')
        dfg.add_count('C', 'B1')
        dfg.add_count('C', 'B2')

        found_choices = find_one_step_choices_in_dfg(dfg)
        expected_choices = [Choice([Singleton('B1'), Singleton('B2')])]

        self.maxDiff = None
        self.assertCountEqual(expected_choices, found_choices)


    def test_find_one_step_choices_in_dfg_complex_case(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('root', 'option1')
        dfg.add_count('root', 'option2')
        dfg.add_count('root', 'end')
        dfg.add_count('root', 'outside1')
        dfg.add_count('outside2', 'root')
        dfg.add_count('option1', 'mid')
        dfg.add_count('option2', 'mid')
        dfg.add_count('mid', 'end')

        found_choices = find_one_step_choices_in_dfg(dfg)

        expected_choices = [
            Choice([Singleton('option1'), Singleton('option2')])
        ]

        self.maxDiff = None
        self.assertCountEqual(expected_choices, found_choices)

    def test_find_one_step_choice_from_branch_candidate_node(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', '1')
        dfg.add_count('1', '2')
        dfg.add_count('1', '5')
        dfg.add_count('2', '4')
        dfg.add_count('2', '6')
        dfg.add_count('4', '5')
        dfg.add_count('5', '12')
        dfg.add_count('5', '13')
        dfg.add_count('6', '7')
        dfg.add_count('6', '8')
        dfg.add_count('8', '11')
        dfg.add_count('8', '9')
        dfg.add_count('12', '14')
        dfg.add_count('13', '14')

        found_choice = find_one_step_choice_from_branch_candidate_node(
                dfg, dfg.nodes['5'])
        self.assertEqual(None, found_choice)

        found_choice = find_one_step_choice_from_branch_candidate_node(
                dfg, dfg.nodes['12'])
        self.assertEqual(Choice([Singleton('12'), Singleton('13')]), found_choice)

    def test_find_one_step_choices_before_parallel(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B')
        dfg.add_count('A', 'C')
        dfg.add_count('B', 'D')
        dfg.add_count('B', 'E')
        dfg.add_count('C', 'D')
        dfg.add_count('C', 'E')
        dfg.add_count('D', 'E')
        dfg.add_count('D', 'F')
        dfg.add_count('D', 'G')
        dfg.add_count('E', 'D')
        dfg.add_count('E', 'F')
        dfg.add_count('E', 'G')
        dfg.add_count('F', 'E')
        dfg.add_count('F', 'G')
        dfg.add_count('G', 'D')
        dfg.add_count('G', 'F')

        found_choices = find_one_step_choices_in_dfg(dfg)

        expected_choices = [
            Choice([Singleton('B'), Singleton('C')])
        ]

        self.maxDiff = None
        self.assertCountEqual(expected_choices, found_choices)

if __name__ == '__main__':
    unittest.main()