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
from prolothar_common.models.data_petri_net import DataPetriNet, Transition, Place

class TestSequence(unittest.TestCase):

    def test_add_to_petri_net(self):
        petri_net = DataPetriNet()

        sequence = Sequence.from_activity_list(['A', 'B', 'C'])

        sequence.add_to_petri_net(petri_net)
        petri_net.prune()

        expected_petri_net = DataPetriNet()

        pre_A = expected_petri_net.add_place(Place.with_empty_label('__pre__A'))
        post_A = expected_petri_net.add_place(Place.with_empty_label('__pre__B'))
        post_B = expected_petri_net.add_place(Place.with_empty_label('__pre__C'))
        post_C = expected_petri_net.add_place(Place.with_empty_label('__post__C'))

        A = expected_petri_net.add_transition(Transition('A'))
        B = expected_petri_net.add_transition(Transition('B'))
        C = expected_petri_net.add_transition(Transition('C'))

        expected_petri_net.add_connection(pre_A, A, post_A)
        expected_petri_net.add_connection(post_A, B, post_B)
        expected_petri_net.add_connection(post_B, C, post_C)

        self.maxDiff = None
        self.assertEqual(petri_net.plot(view=False),
                         expected_petri_net.plot(view=False))

    def test_fold_dfg_mid_connection(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'C')
        dfg.add_count('D', 'B')
        dfg.add_count('D', 'A')

        folded_dfg = dfg.fold([
            Sequence.from_activity_list(['A','B','C'])
        ])

        expected_folded_dfg = PatternDfg()

        expected_folded_dfg.add_count('D', '[A,B,C]')

        self.assertEqual(expected_folded_dfg, folded_dfg)

    def test_fold_dfg_mid_connection_2(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'C')
        dfg.add_count('D', 'B')

        folded_dfg = dfg.fold([
            Sequence.from_activity_list(['A','B','C'])
        ])

        expected_folded_dfg = PatternDfg()
        expected_folded_dfg.add_node('D')
        expected_folded_dfg.add_node('[A,B,C]')

        self.assertEqual(expected_folded_dfg, folded_dfg)

    def test_contains_activity_noisy_sequence(self):
        sequence = Sequence([Singleton('A'), Singleton('B')],
                             special_noise_set={'C'})
        self.assertFalse(sequence.contains_activity('D'))
        self.assertTrue(sequence.contains_activity('A'))
        self.assertTrue(sequence.contains_activity('B'))
        self.assertTrue(sequence.contains_activity('C'))

if __name__ == '__main__':
    unittest.main()