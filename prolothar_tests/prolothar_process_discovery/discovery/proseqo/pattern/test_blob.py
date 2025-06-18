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
from prolothar_process_discovery.discovery.proseqo.pattern.blob import Blob
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_common.models.data_petri_net import DataPetriNet
from prolothar_common.models.nested_graph import NestedGraph

class TestBlob(unittest.TestCase):

    def test_fold_dfg(self):
        dfg = PatternDfg()

        #non-blob
        dfg.add_count('a', 'b')
        dfg.add_count('b', 'c')
        dfg.add_count('c', 'd')
        dfg.add_count('d', 'e')
        dfg.add_count('e', 'f')

        #blob
        dfg.add_count('l', 'h')
        dfg.add_count('l', 'k')
        dfg.add_count('h', 'k')
        dfg.add_count('h', 'l')
        dfg.add_count('h', 'g')
        dfg.add_count('k', 'g')
        dfg.add_count('k', 'l')
        dfg.add_count('k', 'h')
        dfg.add_count('g', 'l')
        dfg.add_count('g', 'h')

        #blob to non-blob
        dfg.add_count('k', 'e')
        dfg.add_count('l', 'e')
        dfg.add_count('h', 'e', count=7)

        #non-blob to blob
        dfg.add_count('c', 'k')
        dfg.add_count('c', 'g', count=3)
        dfg.add_count('c', 'h')

        dfg_with_blob = dfg.fold({
            Blob({'g', 'h', 'k', 'l'})
        ])


        expected_dfg = PatternDfg()
        expected_dfg.add_count('a', 'b')
        expected_dfg.add_count('b', 'c')
        expected_dfg.add_count('c', 'd')
        expected_dfg.add_count('d', 'e')
        expected_dfg.add_count('e', 'f')
        expected_dfg.add_count('{g,h,k,l}', 'e', count=9)
        expected_dfg.add_count('c', '{g,h,k,l}', count=5)

        self.assertEqual(
                expected_dfg.plot(view=False, show_counts=True),
                dfg_with_blob.plot(view=False, show_counts=True))

    def test_fold_optional_blob_in_dfg(self):
        dfg = PatternDfg()

        #non-blob
        dfg.add_count('a', 'b')
        dfg.add_count('b', 'c')
        dfg.add_count('c', 'd')
        dfg.add_count('d', 'e')
        dfg.add_count('e', 'f')
        #skip blob
        dfg.add_count('c', 'e')

        #blob
        dfg.add_count('l', 'h')
        dfg.add_count('l', 'k')
        dfg.add_count('h', 'k')
        dfg.add_count('h', 'l')
        dfg.add_count('h', 'g')
        dfg.add_count('k', 'g')
        dfg.add_count('k', 'l')
        dfg.add_count('k', 'h')
        dfg.add_count('g', 'l')
        dfg.add_count('g', 'h')

        #blob to non-blob
        dfg.add_count('k', 'e')
        dfg.add_count('l', 'e')
        dfg.add_count('h', 'e', count=7)

        #non-blob to blob
        dfg.add_count('c', 'k')
        dfg.add_count('c', 'g', count=3)
        dfg.add_count('c', 'h')

        dfg_with_blob = dfg.fold({
            Optional(Blob({'g', 'h', 'k', 'l'}))
        ])

        expected_dfg = PatternDfg()
        expected_dfg.add_count('a', 'b')
        expected_dfg.add_count('b', 'c')
        expected_dfg.add_count('c', 'd')
        expected_dfg.add_count('d', 'e')
        expected_dfg.add_count('e', 'f')
        expected_dfg.add_count('{g,h,k,l}?', 'e', count=10)
        expected_dfg.add_count('c', '{g,h,k,l}?', count=6)

        self.assertEqual(
                expected_dfg.plot(view=False, show_counts=True),
                dfg_with_blob.plot(view=False, show_counts=True))

    def test_fold_optional_blob_in_already_folded_dfg(self):
        dfg = PatternDfg()

        #non-blob
        dfg.add_count('a', 'b')
        dfg.add_count('b', 'c')
        dfg.add_count('c', 'd')
        dfg.add_count('d', 'e')
        dfg.add_count('e', 'f')
        #skip blob
        dfg.add_count('c', 'e')

        #blob
        dfg.add_count('l', 'h')
        dfg.add_count('l', 'k')
        dfg.add_count('h', 'k')
        dfg.add_count('h', 'l')
        dfg.add_count('h', 'g')
        dfg.add_count('k', 'g')
        dfg.add_count('k', 'l')
        dfg.add_count('k', 'h')
        dfg.add_count('g', 'l')
        dfg.add_count('g', 'h')

        #blob to non-blob
        dfg.add_count('k', 'e')
        dfg.add_count('l', 'e')
        dfg.add_count('h', 'e', count=7)

        #non-blob to blob
        dfg.add_count('c', 'k')
        dfg.add_count('c', 'g', count=3)
        dfg.add_count('c', 'h')

        dfg_with_blob = dfg.fold({
            Blob({'g', 'h', 'k', 'l'})
        ])
        dfg_with_blob = dfg_with_blob.fold({
            Optional(Blob({'g', 'h', 'k', 'l'}))
        ])

        expected_dfg = PatternDfg()
        expected_dfg.add_count('a', 'b')
        expected_dfg.add_count('b', 'c')
        expected_dfg.add_count('c', 'd')
        expected_dfg.add_count('d', 'e')
        expected_dfg.add_count('e', 'f')
        expected_dfg.add_count('{g,h,k,l}?', 'e', count=10)
        expected_dfg.add_count('c', '{g,h,k,l}?', count=6)

        self.assertEqual(
                expected_dfg.plot(view=False, show_counts=True),
                dfg_with_blob.plot(view=False, show_counts=True))

    def test_expand_dfg(self):
        folded_dfg = PatternDfg()
        folded_dfg.add_count('c', 'd')
        folded_dfg.add_count('d', 'e')
        folded_dfg.add_count('{g,h,k}', 'e')
        folded_dfg.add_count('c', '{g,h,k}')
        folded_dfg.add_pattern('{g,h,k}', Blob({'g', 'h', 'k'}))

        expanded_dfg = folded_dfg.expand()

        dfg = PatternDfg()
        dfg.add_count('c', 'd')
        dfg.add_count('d', 'e')
        dfg.add_count('k', 'e')
        dfg.add_count('h', 'e')
        dfg.add_count('g', 'e')
        dfg.add_count('k', 'h')
        dfg.add_count('k', 'g')
        dfg.add_count('h', 'k')
        dfg.add_count('h', 'g')
        dfg.add_count('g', 'k')
        dfg.add_count('g', 'h')
        dfg.add_count('c', 'k')
        dfg.add_count('c', 'g')
        dfg.add_count('c', 'h')
        for edge in dfg.get_edges():
            edge.count = 0

        self.assertEqual(expanded_dfg, dfg)

    def test_add_to_petri_net(self):
        petri_net = DataPetriNet()

        blob = Blob({'a', 'b', 'c', 'd'})

        blob.add_to_petri_net(petri_net)
        petri_net.prune()

        self.assertEqual(20, len(petri_net.transitions))
        self.assertEqual(6, len(petri_net.places))

        sources = petri_net.get_source_sink_places()[0]
        self.assertEqual(1, len(sources))
        next(iter(sources)).increment_nr_of_tokens()
        fireable_transitions = petri_net.get_fireable_transitions()
        self.assertCountEqual(
                ['a', 'b', 'c', 'd'],
                [t.label for t in fireable_transitions])
        petri_net.force_transition(fireable_transitions[0].id)
        fired_transition = fireable_transitions[0]
        fireable_transitions = petri_net.get_fireable_transitions()
        self.assertCountEqual(
                set(['a', 'b', 'c', 'd', '']).difference([fired_transition.label]),
                [t.label for t in fireable_transitions])

    def test_to_nested_graph(self):
        dfg = PatternDfg()
        dfg.add_count('0', '{A,B,C}')
        dfg.add_count('{A,B,C}', '1')
        dfg.add_pattern('{A,B,C}', Blob({'A','B','C'}))

        expected_graph = NestedGraph()
        expected_graph.add_node(NestedGraph.Node(
                '0', '0', parent=None, attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '1', '{A,B,C}', parent=None, attributes={'pattern_type': 'Blob'}))
        expected_graph.add_node(NestedGraph.Node(
                '1.0', 'A', parent='1', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '1.1', 'B', parent='1', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '1.2', 'C', parent='1', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '2', '0', parent=None, attributes={'pattern_type': 'Singleton'}))

        expected_graph.add_edge(NestedGraph.Edge('0->1', '0', '1'))
        expected_graph.add_edge(NestedGraph.Edge('1.0->1.1', '1.0', '1.1'))
        expected_graph.add_edge(NestedGraph.Edge('1.0->1.2', '1.0', '1.2'))
        expected_graph.add_edge(NestedGraph.Edge('1.1->1.0', '1.1', '1.0'))
        expected_graph.add_edge(NestedGraph.Edge('1.1->1.2', '1.1', '1.2'))
        expected_graph.add_edge(NestedGraph.Edge('1.2->1.0', '1.2', '1.0'))
        expected_graph.add_edge(NestedGraph.Edge('1.2->1.1', '1.2', '1.1'))
        expected_graph.add_edge(NestedGraph.Edge('1->2', '1', '2'))

        actual_graph = dfg.to_nested_graph()
        for edge in actual_graph.get_edges():
            edge.attributes = {}

        self.assertEqual(expected_graph, actual_graph)

if __name__ == '__main__':
    unittest.main()