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
from prolothar_process_discovery.discovery.proseqo.pattern.loop import Loop
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_common.models.data_petri_net import DataPetriNet

from random import Random

class TestLoop(unittest.TestCase):

    def test_remove_activity_and_without_degeneration(self):
        loop = Loop(Sequence.from_activity_list(['A', 'B']))

        loop.remove_activity('A')
        self.assertEqual(1, loop.get_nr_of_subpatterns())

        self.assertFalse(loop.subpattern.is_singleton())
        loop = loop.without_degeneration()[0]
        self.assertTrue(loop.subpattern.is_singleton())

        try:
            loop.remove_activity('B')
            self.assertFail('should lead to ValueError')
        except ValueError:
            pass

    def test_fold_and_expand_dfg_singleton(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B', count=2)
        dfg.add_count('B', 'B')
        dfg.add_count('B', 'C', count=3)

        folded_dfg = dfg.fold({Loop(Singleton('B'))])

        expected_folded_dfg = PatternDfg()
        expected_folded_dfg.add_count('A', 'B+', count=2)
        expected_folded_dfg.add_count('B+', 'C', count=3)

        self.assertEqual(expected_folded_dfg, folded_dfg)

        expected_expanded_dfg = PatternDfg()
        expected_expanded_dfg.add_count('A', 'B', count=0)
        expected_expanded_dfg.add_count('B', 'B', count=0)
        expected_expanded_dfg.add_count('B', 'C', count=0)

        expanded_dfg = folded_dfg.expand()
        self.assertEqual(expected_expanded_dfg, expanded_dfg)

    def test_fold_and_expand_dfg_sequence(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'C')
        dfg.add_count('C', 'B')
        dfg.add_count('C', 'D')

        folded_dfg = dfg.fold({Loop(Sequence.from_activity_list(['B', 'C']))])

        expected_folded_dfg = PatternDfg()
        expected_folded_dfg.add_count('A', '[B,C]+')
        expected_folded_dfg.add_count('[B,C]+', 'D')

        self.assertEqual(expected_folded_dfg, folded_dfg)

        expected_expanded_dfg = PatternDfg()
        expected_expanded_dfg.add_count('A', 'B', count=0)
        expected_expanded_dfg.add_count('B', 'C', count=0)
        expected_expanded_dfg.add_count('C', 'B', count=0)
        expected_expanded_dfg.add_count('C', 'D', count=0)

        expanded_dfg = folded_dfg.expand()
        self.assertEqual(expected_expanded_dfg, expanded_dfg)

    def test_add_to_petri_net(self):
        petri_net = DataPetriNet()

        loop = Loop(Sequence.from_activity_list(['A', 'B']))

        loop.add_to_petri_net(petri_net)
        petri_net.prune()

        self.assertEqual(5, len(petri_net.transitions))
        self.assertEqual(5, len(petri_net.places))

    def test_merge_subpatterns(self):
        """
        [x+,y?]+ should be reduced to [x,y?]+
        """
        pattern = Loop(Sequence([
            Loop(Singleton('x')),
            Optional(Singleton('y'))
        ]))
        self.assertTrue(pattern.merge_subpatterns())

        expected_pattern = Loop(Sequence([
            Singleton('x'),
            Optional(Singleton('y'))
        ]))

        self.assertEqual(pattern, expected_pattern)

    def test_generate_activities(self):
        loop = Loop(Sequence.from_activity_list(['f', 'g']))
        self.assertListEqual(
                ['f', 'g', 'f', 'g', 'f', 'g'],
                loop.generate_activities(random=Random(42)))
        self.assertListEqual(
                ['f', 'g'],
                loop.generate_activities(random=Random(24)))
        self.assertListEqual(
                ['f', 'g', 'f', 'g'],
                loop.generate_activities(random=Random(54)))

if __name__ == '__main__':
    unittest.main()