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
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.closed_communities import find_closed_communities_in_dfg
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

class TestClosedCommunities(unittest.TestCase):

    def test_find_closed_communities_in_dfg(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', '1')
        dfg.add_count('1', '2')
        dfg.add_count('2', '4')
        dfg.add_count('2', '6')
        dfg.add_count('4', '5')
        dfg.add_count('5', '1')
        dfg.add_count('6', '7')
        dfg.add_count('7', '8')
        dfg.add_count('8', '6')
        dfg.add_count('8', '9')
        dfg.add_count('9', '10')
        dfg.add_count('10', '11')

        found_communities = find_closed_communities_in_dfg(dfg)

        community_1 = SubGraph(PatternDfg.create_from_dfg(
                dfg.select_nodes(['0', '1', '2', '4', '5', '6', '7', '8', '9'])),
                ['0'], ['9']
        )

        community_2 = SubGraph(PatternDfg.create_from_dfg(
                dfg.select_nodes(['10', '11'])), ['10'], ['11'])

        self.assertCountEqual([community_1, community_2], found_communities)

    def test_find_closed_communities_in_dfg_wabenhistorie_excerpt(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('[BRWA,STOE,STOZ]', 'WLVG')
        dfg.add_count('[HWOE,HWOZ]', 'WLVG')
        dfg.add_count('[HWOE,HWOZ]', 'WLFG')
        dfg.add_count('WLVG', 'WLFG')
        dfg.add_count('WLFG', 'GREX')
        dfg.add_count('WLFG', 'EACC')
        dfg.add_count('WLFG', 'WRIC')
        dfg.add_count('EACC', 'GREX')
        dfg.add_count('EACC', 'WNEK')
        dfg.add_count('WNEK', 'HSAN?')
        dfg.add_count('WRIC', 'HSAN?')
        dfg.add_count('HSAN?', 'GREX')

        found_communities = find_closed_communities_in_dfg(dfg)

        community_1 = SubGraph(PatternDfg.create_from_dfg(
                dfg.select_nodes(['[BRWA,STOE,STOZ]', '[HWOE,HWOZ]', 'WLVG',
                                  'WLFG'])),
                ['[BRWA,STOE,STOZ]'], ['WLFG'])

        community_2 = PatternDfg.create_from_dfg(
                dfg.select_nodes(['EACC', 'WRIC', 'WNEK', 'HSAN?', 'GREX']))
        community_2 = SubGraph(community_2, ['EACC', 'WRIC', 'GREX'], ['GREX'])

        self.maxDiff = None
        self.assertListEqual(
                [community_1.pattern_dfg, community_2.pattern_dfg],
                [c.pattern_dfg for c in found_communities])

        pattern_dfg = PatternDfg.create_from_dfg(dfg)
        folden_pattern_dfg = pattern_dfg.fold({community_1, community_2])

        for edge in dfg.edges.values():
            edge.count = 0
        self.assertEqual(dfg, folden_pattern_dfg.expand())

    def test_find_closed_communities_with_inner_loop(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'C')
        dfg.add_count('C', 'B')
        dfg.add_count('B', 'D')
        found_communities = find_closed_communities_in_dfg(dfg)
        self.assertEqual(1, len(found_communities))

if __name__ == '__main__':
    unittest.main()
