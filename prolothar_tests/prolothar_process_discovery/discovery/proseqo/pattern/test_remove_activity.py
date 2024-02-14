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
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.pattern.clustering import Clustering

class TestPatternRemoveActivity(unittest.TestCase):

    def test_remove_activity_sequence(self):

        sequence = Sequence.from_activity_list([
                'fill water tank', 'fill coffee', 'take a cup', 'press start',
                'drink'])

        sequence.remove_activity('fill coffee')

        self.assertEqual(Sequence.from_activity_list([
                'fill water tank', 'take a cup', 'press start',
                'drink']), sequence)

        try:
            Sequence.from_activity_list(['A']).remove_activity('A')
            self.fail('sequence must not be empty after removal')
        except ValueError:
            pass

    def test_remove_activity_choice_in_sequence(self):
        sequence = Sequence([Singleton('IBET'),
                             Choice([Singleton('STIB'), Singleton('EZIB')]),
                             Singleton('SIUS')])
        sequence.remove_activity('EZIB')
        self.assertEqual(Sequence([Singleton('IBET'),
                                   Choice([Singleton('STIB')]),
                                   Singleton('SIUS')]),
                         sequence)
        sequence.remove_activity('STIB')
        self.assertEqual(Sequence([Singleton('IBET'),
                                   Singleton('SIUS')]),
                         sequence)
        sequence.remove_activity('IBET')
        try:
            sequence.remove_activity('SIUS')
            self.fail('sequence option must not be empty after removal')
        except ValueError:
            pass

    def test_remove_activity_sequence_nested_in_choice(self):
        choice = Choice([Singleton('11'),
                         Sequence.from_activity_list(['9', '10'])])

        choice.remove_activity('10')

        self.assertEqual(Choice([Singleton('11'),
                                 Sequence.from_activity_list(['9'])]),
                         choice)

    def test_remove_activity_community(self):
        community = PatternDfg()
        community.add_count('1', '2')
        community = SubGraph(community, ['1'], ['2'])

        community.remove_activity('1')
        self.assertEqual(1, community.pattern_dfg.get_nr_of_nodes())
        try:
            community.remove_activity('2')
            self.fail('community must not be empty after removal')
        except ValueError:
            pass


    def test_remove_activity_clustering(self):
        cluster1 = PatternDfg()
        cluster1.add_count('1', '2')
        cluster1 = SubGraph(cluster1, ['1'], ['2'])

        cluster2 = PatternDfg()
        cluster2.add_count('1', '3')
        cluster2 = SubGraph(cluster2, ['1'], ['3'])

        cluster3 = PatternDfg()
        cluster3.add_count('2', '3')
        cluster3 = SubGraph(cluster3, ['2'], ['3'])

        clustering = Clustering([cluster1, cluster2, cluster3],
                                {'1': 0, '2': 0, '3': 0})

        clustering.remove_activity('1')

        self.assertEqual(1, cluster1.get_nr_of_subpatterns())
        self.assertEqual(1, cluster2.get_nr_of_subpatterns())
        self.assertEqual(2, cluster3.get_nr_of_subpatterns())


if __name__ == '__main__':
    unittest.main()