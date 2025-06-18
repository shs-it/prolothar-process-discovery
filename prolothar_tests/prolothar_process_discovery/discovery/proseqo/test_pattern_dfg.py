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
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.pattern.clustering import Clustering
from prolothar_process_discovery.discovery.proseqo.pattern.loop import Loop
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.eventlog import EventLog
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Transition, Place
from prolothar_process_discovery.data.synthetic_baking import baking as synthetic_baking

class TestPatternDfg(unittest.TestCase):

    def test_expand_sequences(self):
        pattern_dfg = PatternDfg()

        pattern_dfg.add_count('start computer', 'program')
        pattern_dfg.add_count('program', 'visit meeting')
        pattern_dfg.add_count('visit meeting', 'drink coffee')
        pattern_dfg.add_count('drink coffee', 'eat lunch')
        pattern_dfg.add_count('eat lunch', 'program')
        pattern_dfg.add_count('eat lunch', 'visit meeting')
        pattern_dfg.add_count('drink coffee', 'program')
        pattern_dfg.add_count('program', 'program')
        pattern_dfg.add_count('program', 'shutdown computer')

        pattern_dfg.add_pattern('drink coffee', Sequence.from_activity_list([
                'fill water tank', 'fill coffee', 'take a cup', 'press start',
                'drink']))

        extended_dfg = pattern_dfg.expand()

        expected_extended_dfg = DirectlyFollowsGraph()
        expected_extended_dfg.add_count('start computer', 'program')
        expected_extended_dfg.add_count('program', 'visit meeting')
        expected_extended_dfg.add_count('visit meeting', 'fill water tank')
        expected_extended_dfg.add_count('fill water tank', 'fill coffee')
        expected_extended_dfg.add_count('fill coffee', 'take a cup')
        expected_extended_dfg.add_count('take a cup', 'press start')
        expected_extended_dfg.add_count('press start', 'drink')
        expected_extended_dfg.add_count('drink', 'eat lunch')
        expected_extended_dfg.add_count('drink', 'program')
        expected_extended_dfg.add_count('eat lunch', 'program')
        expected_extended_dfg.add_count('eat lunch', 'visit meeting')
        expected_extended_dfg.add_count('program', 'program')
        expected_extended_dfg.add_count('program', 'shutdown computer')
        for edge in expected_extended_dfg.edges.values():
            edge.count = 0

        self.assertEqual(expected_extended_dfg, extended_dfg)

    def test_expand_nested_sequence(self):
        pattern_dfg = PatternDfg()
        pattern_dfg.add_count('A', '[IBET,(STIB|EZIB),SIUS]')
        pattern_dfg.add_count('[IBET,(STIB|EZIB),SIUS]', 'B')
        pattern_dfg.add_pattern('[IBET,(STIB|EZIB),SIUS]',
                                Sequence([
                                    Singleton('IBET'),
                                    Choice([Singleton('STIB'), Singleton('EZIB')]),
                                    Singleton('SIUS')]))

        extended_dfg = pattern_dfg.expand()

        expected_extended_dfg = DirectlyFollowsGraph()
        expected_extended_dfg.add_count('A', 'IBET')
        expected_extended_dfg.add_count('IBET', 'STIB')
        expected_extended_dfg.add_count('IBET', 'EZIB')
        expected_extended_dfg.add_count('STIB', 'SIUS')
        expected_extended_dfg.add_count('EZIB', 'SIUS')
        expected_extended_dfg.add_count('SIUS', 'B')
        for edge in expected_extended_dfg.edges.values():
            edge.count = 0

        self.assertEqual(expected_extended_dfg, extended_dfg)

    def test_expand_nested_non_recursive(self):
        community = PatternDfg()
        community.add_count('A', 'END')
        community.add_count('B', 'END')
        community.add_count('A', 'B')

        pattern_dfg = PatternDfg()
        pattern_dfg.add_count('[START,ER Registration]',
                              '[ER Triage,ER Sepsis Triage]')
        pattern_dfg.add_count('[ER Triage,ER Sepsis Triage]',
                              '[{A,B},...,{END}')
        pattern_dfg.add_pattern(
                '[START,ER Registration]',
                Sequence.from_activity_list(['START', 'ER Registration']))
        pattern_dfg.add_pattern(
                '[ER Triage,ER Sepsis Triage]',
                Sequence.from_activity_list(['ER Triage', 'ER Sepsis Triage']))
        pattern_dfg.add_pattern(
                '[{A,B},...,{END}',
                SubGraph(community, ['A', 'B'], ['END']))

        extended_dfg = pattern_dfg.expand(recursive=False)

        expected_extended_dfg = DirectlyFollowsGraph()
        expected_extended_dfg.add_count('START', 'ER Registration')
        expected_extended_dfg.add_count('ER Registration', 'ER Triage')
        expected_extended_dfg.add_count('ER Triage', 'ER Sepsis Triage')
        expected_extended_dfg.add_count('ER Sepsis Triage', 'A')
        expected_extended_dfg.add_count('ER Sepsis Triage', 'B')
        expected_extended_dfg.add_count('A', 'B')
        expected_extended_dfg.add_count('A', 'END')
        expected_extended_dfg.add_count('B', 'END')
        for edge in expected_extended_dfg.edges.values():
            edge.count = 0
        self.assertEqual(expected_extended_dfg, extended_dfg)

    def test_expand_sequences_2(self):
        pattern_dfg = PatternDfg()
        pattern_dfg.add_count('0', '1,2')
        pattern_dfg.add_count('1,2', '4,5')
        pattern_dfg.add_count('1,2', '6')
        pattern_dfg.add_count('4,5', '1,2')
        pattern_dfg.add_count('4,5', '4,5')
        pattern_dfg.add_pattern('1,2', Sequence([Singleton('1'),
                                                       Singleton('2')]))
        pattern_dfg.add_pattern('4,5', Sequence([Singleton('4'),
                                                       Singleton('5')]))

        expected_extended_dfg = PatternDfg()
        expected_extended_dfg.add_count('0', '1')
        expected_extended_dfg.add_count('1', '2')
        expected_extended_dfg.add_count('2', '4')
        expected_extended_dfg.add_count('2', '6')
        expected_extended_dfg.add_count('4', '5')
        expected_extended_dfg.add_count('5', '1')
        expected_extended_dfg.add_count('5', '4')
        for edge in expected_extended_dfg.edges.values():
            edge.count = 0

        extended_dfg = pattern_dfg.expand()

        self.assertEqual(expected_extended_dfg, extended_dfg)

    def test_fold_sequences(self):
        dfg = PatternDfg()
        dfg.add_count('0', '1', count=3)
        dfg.add_count('1', '2')
        dfg.add_count('2', '4')
        dfg.add_count('2', '6')
        dfg.add_count('4', '5')
        dfg.add_count('5', '1')
        dfg.add_count('5', '4')

        folden_dfg = dfg.fold({Sequence.from_activity_list(['1','2']),
                               Sequence.from_activity_list(['4','5'])})

        pattern_dfg = PatternDfg()
        pattern_dfg.add_count('0', '[1,2]', count=3)
        pattern_dfg.add_count('[1,2]', '[4,5]')
        pattern_dfg.add_count('[1,2]', '6')
        pattern_dfg.add_count('[4,5]', '[1,2]')
        pattern_dfg.add_count('[4,5]', '[4,5]')
        pattern_dfg.add_pattern('[1,2]', Sequence([Singleton('1'),
                                                   Singleton('2')]))
        pattern_dfg.add_pattern('[4,5]', Sequence([Singleton('4'),
                                                   Singleton('5')]))

        self.assertEqual(pattern_dfg, folden_dfg)
        self.assertEqual(Sequence([Singleton('4'), Singleton('5')]),
                         folden_dfg.nodes['[4,5]'].pattern)
        self.assertEqual(Sequence([Singleton('1'), Singleton('2')]),
                         folden_dfg.nodes['[1,2]'].pattern)

        for edge in dfg.edges.values():
            edge.count = 0
        self.assertEqual(folden_dfg.expand(), dfg)

    def test_fold_and_expand_choice(self):
        dfg = PatternDfg()
        dfg.add_count('2', '5')
        dfg.add_count('2', '8')
        dfg.add_count('5', '12')
        dfg.add_count('5', '13')
        dfg.add_count('8', '11')
        dfg.add_count('8', '9')
        dfg.add_count('9', '10')
        dfg.add_count('12', '14')
        dfg.add_count('13', '14')

        folden_dfg = dfg.fold({Choice([Singleton('11'),
                                      Sequence.from_activity_list(['9', '10'])]),
                               Choice([Singleton('12'), Singleton('13')])})

        expected_folden_dfg = PatternDfg()
        expected_folden_dfg.add_count('2', '5')
        expected_folden_dfg.add_count('2', '8')
        expected_folden_dfg.add_count('5', '(12|13)', count=2)
        expected_folden_dfg.add_count('8', '(11|[9,10])', count=2)
        expected_folden_dfg.add_count('(12|13)', '14', count=2)

        self.assertEqual(expected_folden_dfg, folden_dfg)
        self.assertEqual(Choice([Singleton('11'),
                                Sequence.from_activity_list(['9', '10'])]),
                         folden_dfg.nodes['(11|[9,10])'].pattern)
        self.assertEqual(Choice([Singleton('12'), Singleton('13')]),
                         folden_dfg.nodes['(12|13)'].pattern)

    def test_fold_and_expand_optional(self):
        dfg = PatternDfg()
        dfg.add_count('1', '2')
        dfg.add_count('1', '5')
        dfg.add_count('2', '5')
        dfg.add_count('2', '6')
        dfg.add_count('6', '8', count=3)
        dfg.add_count('6', '9', count=4)
        dfg.add_count('8', '9', count=5)

        folden_dfg = dfg.fold({Optional(Singleton('8'))})
        expected_folden_dfg = PatternDfg()
        expected_folden_dfg.add_count('1', '2')
        expected_folden_dfg.add_count('1', '5')
        expected_folden_dfg.add_count('2', '5')
        expected_folden_dfg.add_count('2', '6')
        expected_folden_dfg.add_count('6', '8?', count=7)
        expected_folden_dfg.add_count('8?', '9', count=9)

        self.assertEqual(expected_folden_dfg, folden_dfg)
        self.assertEqual(Optional(Singleton('8')),
                         folden_dfg.nodes['8?'].pattern)

        for edge in dfg.edges.values():
            edge.count = 0
        self.assertEqual(folden_dfg.expand(), dfg)

    def test_fold_and_expand_closed_community(self):
        dfg = PatternDfg()
        dfg.add_count('1', '2')
        dfg.add_count('1', '3')
        dfg.add_count('3', '4')
        dfg.add_count('2', '4')
        dfg.add_count('4', '6')
        dfg.add_count('5', '4')
        dfg.add_count('6', '8')
        dfg.add_count('6', '9')
        dfg.add_count('8', '9')

        community_1 = SubGraph(PatternDfg.create_from_dfg(
                dfg.select_nodes(['1', '2', '3', '4', '5'])), ['1','5'], ['4'])
        community_2 = SubGraph(PatternDfg.create_from_dfg(
                dfg.select_nodes(['6', '8', '9'])), ['6'], ['9'])

        folden_dfg = dfg.fold({community_1, community_2})

        expected_folden_dfg = PatternDfg()
        expected_folden_dfg.add_count('[{1,5},...,{4}]', '[{6},...,{9}]')

        self.assertEqual(expected_folden_dfg, folden_dfg)
        self.assertEqual(community_1, folden_dfg.nodes['[{1,5},...,{4}]'].pattern)
        self.assertEqual(community_2, folden_dfg.nodes['[{6},...,{9}]'].pattern)

        for edge in dfg.edges.values():
            edge.count = 0
        self.assertEqual(folden_dfg.expand(), dfg)

    def test_contains_non_singleton_pattern(self):
        dfg = PatternDfg()
        dfg.add_count('1', '2')
        dfg.add_count('1', '3')
        dfg.add_count('3', '4')
        dfg.add_count('2', '4')
        dfg.add_count('4', '6')
        dfg.add_count('5', '4')
        dfg.add_count('6', '8')
        dfg.add_count('6', '9')
        dfg.add_count('8', '9')

        self.assertFalse(dfg.contains_non_singleton_pattern())

        dfg.add_pattern('8', Sequence.from_activity_list(['a', 'b']))
        self.assertTrue(dfg.contains_non_singleton_pattern())

    def test_fold_and_expand_clustering(self):
        log = EventLog.create_from_simple_activity_log([
            ['A', '1', '2', 'E'],
            ['A', '1', '3', 'E'],
            ['A', '2', '3', 'E'],
            ['A', '1', '3', '2', 'E'],
            ['A', '1', 'E'],
        ])
        dfg = PatternDfg.create_from_event_log(log)

        cluster1 = PatternDfg()
        cluster1.add_count('1', '2')
        cluster1 = SubGraph(cluster1, ['1'], ['2'])

        cluster2 = PatternDfg()
        cluster2.add_count('1', '3')
        cluster2 = SubGraph(cluster2, ['1'], ['3'])

        cluster3 = PatternDfg()
        cluster3.add_count('2', '3')
        cluster3 = SubGraph(cluster3, ['2'], ['3'])

        cluster_pattern = Clustering([cluster1, cluster2, cluster3], {
            log.traces[0]: 0,
            log.traces[1]: 1,
            log.traces[2]: 2,
            log.traces[3]: 1,
            log.traces[4]: 0,
        })

        cluster_name = '([{1},...,{2}]|[{1},...,{3}]|[{2},...,{3}])'
        expected_folden_dfg = PatternDfg()
        expected_folden_dfg.add_count('A', cluster_name)
        expected_folden_dfg.add_count(cluster_name, 'E')
        expected_folden_dfg.add_pattern(cluster_name, cluster_pattern)

        folden_dfg = dfg.fold({cluster_pattern})

        self.assertEqual(expected_folden_dfg, folden_dfg)
        self.assertEqual(cluster_pattern, folden_dfg.nodes[cluster_name].pattern)

    def test_fold_and_expand_clustering_and_closed_community(self):
        log = synthetic_baking.generate_log(100, use_clustering_model=True)
        dfg = PatternDfg.create_from_event_log(log)

        cluster1 = Sequence.from_activity_list([
                'Start', 'Add Eggs', 'Add Sugar', 'Beat up Foamy', 'Add Flour',
                'Fold in', 'Put into Oven'])

        cluster2 = Sequence.from_activity_list([
                'Start', 'Add Milk', 'Add Butter', 'Stir', 'Stir in Flour',
                'Add Baking Powder', 'Add Yeast', 'Put into Oven'])

        trace_cluster_dict = {}
        for trace in log.traces:
            if trace.contains_activity('Fold in'):
                trace_cluster_dict[trace] = 0
            else:
                trace_cluster_dict[trace] = 1
        clustering = Clustering([cluster1, cluster2], trace_cluster_dict)

        community_pdfg = PatternDfg()
        community_pdfg.add_count('Read a Book', 'Check Time')
        community_pdfg.add_count('Watch TV', 'Check Time')
        community_pdfg.add_count('Check Time', 'Read a Book')
        community_pdfg.add_count('Check Time', 'Watch TV')
        community_pdfg.add_count('Check Time', ('[Take out of the Oven,'
                                                'Sprinkle with Icing Sugar?,'
                                                '[Eat,Smile,End]]'))
        community_pdfg.add_pattern(
                '[Take out of the Oven,Sprinkle with Icing Sugar?,[Eat,Smile,End]]',
                Sequence([Singleton('Take out of the Oven'),
                          Optional(Singleton('Sprinkle with Icing Sugar')),
                          Sequence.from_activity_list(['Eat', 'Smile', 'End'])]))

        community = SubGraph(
                community_pdfg, ['Read a Book', 'Watch TV'],
                ['[Take out of the Oven,Sprinkle with Icing Sugar?,[Eat,Smile,End]]'])

        folded_dfg = dfg.fold({clustering, community})

        self.assertEqual(2, folded_dfg.get_nr_of_nodes())
        self.assertEqual(1, folded_dfg.get_nr_of_edges())

    def test_fold_choice_with_double_links(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B1')
        dfg.add_count('A', 'B2')
        dfg.add_count('B1', 'C')
        dfg.add_count('B2', 'C')
        dfg.add_count('C', 'B1')
        dfg.add_count('C', 'B2')

        choice_pattern = Choice([Singleton('B1'), Singleton('B2')])

        folded_dfg = dfg.fold({choice_pattern})

        expected_dfg = PatternDfg()
        expected_dfg.add_count('A', '(B1|B2)', count=2)
        expected_dfg.add_count('(B1|B2)', 'C', count=2)
        expected_dfg.add_count('C', '(B1|B2)', count=2)
        expected_dfg.add_pattern('(B1|B2)', choice_pattern)

        self.assertEqual(folded_dfg, expected_dfg)

    def test_fold_and_expand_nested(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'C')
        dfg.add_count('C', 'D')
        dfg.add_count('C', 'E')
        dfg.add_count('D', 'F')
        dfg.add_count('E', 'G')
        dfg.add_count('E', 'H')
        dfg.add_count('F', 'H')
        dfg.add_count('G', 'H')
        dfg.add_count('H', 'I')

        start_list_pattern = Sequence.from_activity_list(['A', 'B', 'C'])
        nested_pattern = Choice([
                Sequence([Singleton('D'), Singleton('F')]),
                Sequence([Singleton('E'), Optional(Singleton('G'))])])
        end_list_pattern = Sequence.from_activity_list(['H', 'I'])
        folden_dfg = dfg.fold({start_list_pattern, nested_pattern,
                               end_list_pattern})

        expected_folden_dfg = PatternDfg()
        expected_folden_dfg.add_count('[A,B,C]', '([D,F]|[E,G?])', count=2)
        expected_folden_dfg.add_count('([D,F]|[E,G?])', '[H,I]', count=3)

        self.assertEqual(expected_folden_dfg, folden_dfg)

        for edge in dfg.edges.values():
            edge.count = 0
        self.assertEqual(folden_dfg.expand(), dfg)

    def test_pattern_is_singleton(self):
        self.assertTrue(Singleton('a').is_singleton())
        self.assertFalse(Sequence([Singleton('a'),Singleton('b')]).is_singleton())
        self.assertFalse(Choice([Singleton('a'),Singleton('b')]).is_singleton())

    def test_fold_and_expand_complex(self):
        community_dfg = PatternDfg()
        community_dfg.add_count('Leucocytes+', 'CRP+')
        community_dfg.add_count('IV Liquid', 'IV Antibiotics')
        community_dfg.add_count('IV Liquid', 'Admission NC+')
        community_dfg.add_count('IV Antibiotics', 'IV Liquid')
        community_dfg.add_count('IV Antibiotics', 'Admission NC+')
        community_dfg.add_count('IV Antibiotics', 'Leucocytes+')
        community_dfg.add_count('IV Antibiotics', 'END')
        community_dfg.add_count('CRP+', 'Leucocytes+')
        community_dfg.add_count('CRP+', 'LacticAcid')
        community_dfg.add_count('CRP+', '[Release A,Return ER?]')
        community_dfg.add_count('LacticAcid', 'IV Liquid')
        community_dfg.add_count('LacticAcid', 'Admission NC+')
        community_dfg.add_count('LacticAcid', 'IV Antibiotics')
        community_dfg.add_count('[Release A,Return ER?]', 'END')
        community_dfg.add_count('Admission NC+', 'CRP+')
        community_dfg.add_pattern('Leucocytes+', Loop(Singleton('Leucocytes')))
        community_dfg.add_pattern('CRP+', Loop(Singleton('CRP')))
        community_dfg.add_pattern('Admission NC+', Loop(Singleton('Admission NC')))
        community_dfg.add_pattern(
                '[Release A,Return ER?]',
                Sequence([Singleton('Release A'), Optional(Singleton('Return ER'))]))



        dfg = PatternDfg()
        dfg.add_count('[START,ER Registration]',
                      '[ER Triage,ER Sepsis Triage]')
        dfg.add_count('[ER Triage,ER Sepsis Triage]',
                      '[{CRP+,IV Liquid,IV Antibiotics},...,{END}]')
        dfg.add_pattern(
                '[START,ER Registration]',
                Sequence.from_activity_list(['START', 'ER Registration']))
        dfg.add_pattern(
                '[ER Triage,ER Sepsis Triage]',
                Sequence.from_activity_list(['ER Triage', 'ER Sepsis Triage']))
        dfg.add_pattern(
                '[{CRP+,IV Liquid,IV Antibiotics},...,{END}]', SubGraph(
                        community_dfg, ['CRP+','IV Liquid','IV Antibiotics'], ['END']))

        expanded_dfg = dfg.expand(recursive=False)
        self.assertEqual(12, expanded_dfg.get_nr_of_nodes())

    def test_create_from_dfg(self):
        dfg = DirectlyFollowsGraph()
        dfg.add_count('0', '1')
        dfg.add_count('1', '2')
        dfg.add_count('2', '4')
        dfg.add_count('2', '6')
        dfg.add_count('4', '5')
        dfg.add_count('5', '1')
        dfg.add_count('5', '4')

        pattern_dfg = PatternDfg.create_from_dfg(dfg)

        self.assertEqual(dfg.plot(view=False),
                         pattern_dfg.plot(view=False))

        for node in pattern_dfg.get_nodes():
            self.assertTrue(node.pattern is not None)

    def test_to_and_from_nested_graph(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'C')
        dfg.add_count('C', 'D')
        dfg.add_count('C', 'E')
        dfg.add_count('D', 'F')
        dfg.add_count('E', 'G')
        dfg.add_count('E', 'H')
        dfg.add_count('F', 'H')
        dfg.add_count('G', 'H')
        dfg.add_count('H', 'I')

        start_list_pattern = Sequence.from_activity_list(['A', 'B', 'C'])
        nested_pattern = Choice([
                Sequence([Singleton('D'), Singleton('F')]),
                Sequence([Singleton('E'), Optional(Singleton('G'))])])
        end_list_pattern = Sequence.from_activity_list(['H', 'I'])
        folded_dfg = dfg.fold({start_list_pattern, nested_pattern,
                               end_list_pattern})

        expected_graph = NestedGraph()
        expected_graph.add_node(NestedGraph.Node(
                '0', '[A,B,C]', attributes={'pattern_type': 'Sequence'}))
        expected_graph.add_node(NestedGraph.Node(
                '0.0', 'A', parent='0', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '0.1', 'B', parent='0', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '0.2', 'C', parent='0', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '1', '([D,F]|[E,G?])', attributes={'pattern_type': 'Choice'}))
        expected_graph.add_node(NestedGraph.Node(
                '1.0', '[D,F]', parent='1', attributes={'pattern_type': 'Sequence'}))
        expected_graph.add_node(NestedGraph.Node(
                '1.0.0', 'D', parent='1.0', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '1.0.1', 'F', parent='1.0', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '1.1', '[E,G?]', parent='1', attributes={'pattern_type': 'Sequence'}))
        expected_graph.add_node(NestedGraph.Node(
                '1.1.0', 'E', parent='1.1', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '1.1.1', 'G?', parent='1.1', attributes={'pattern_type': 'Optional'}))
        expected_graph.add_node(NestedGraph.Node(
                '1.1.1.0', 'G', parent='1.1.1', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '2', '[H,I]', attributes={'pattern_type': 'Sequence'}))
        expected_graph.add_node(NestedGraph.Node(
                '2.0', 'H', parent='2', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_node(NestedGraph.Node(
                '2.1', 'I', parent='2', attributes={'pattern_type': 'Singleton'}))
        expected_graph.add_edge(NestedGraph.Edge(
                '0.0->0.1', '0.0', '0.1'))
        expected_graph.add_edge(NestedGraph.Edge(
                '0.1->0.2', '0.1', '0.2'))
        expected_graph.add_edge(NestedGraph.Edge(
                '1.0.0->1.0.1', '1.0.0', '1.0.1'))
        expected_graph.add_edge(NestedGraph.Edge(
                '1.1.0->1.1.1', '1.1.0', '1.1.1'))
        expected_graph.add_edge(NestedGraph.Edge(
                '2.0->2.1', '2.0', '2.1'))
        expected_graph.add_edge(NestedGraph.Edge(
                '0->1', '0', '1', attributes={'count': 2}))
        expected_graph.add_edge(NestedGraph.Edge(
                '1->2', '1', '2', attributes={'count': 3}))

        self.assertEqual(expected_graph, folded_dfg.to_nested_graph())

        parsed_pattern_graph = PatternDfg.create_from_nested_graph(expected_graph)
        self.assertEqual(folded_dfg, parsed_pattern_graph)

    def test_to_and_from_nested_graph_with_long_sequence(self):
        pattern = Sequence.from_activity_list(list(str(i) for i in range(20)))
        pattern_dfg = PatternDfg()
        pattern_dfg.add_node(pattern.get_activity_name())
        pattern_dfg.add_pattern(pattern.get_activity_name(), pattern)
        restored_pattern_dfg = PatternDfg.create_from_nested_graph(
                pattern_dfg.to_nested_graph())
        self.assertEqual(pattern_dfg, restored_pattern_dfg)

        node = pattern_dfg.nodes[pattern.get_activity_name()]
        restored_node = restored_pattern_dfg.nodes[pattern.get_activity_name()]
        self.assertEqual(node.pattern, restored_node.pattern)

    def test_remove_degenerated_patterns(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'C')
        dfg.add_count('C', 'D')
        dfg.add_count('D', 'E')
        dfg.add_count('E', 'F')
        dfg.add_count('F', 'G')

        dfg.add_pattern('A', Sequence([Singleton('a')]))
        dfg.add_pattern('B', Sequence([Sequence([Singleton('b')])]))
        dfg.add_pattern('C', Optional(Optional(Singleton('c'))))
        dfg.add_pattern('D', Optional(Sequence([Singleton('d')])))
        dfg.add_pattern('E', Optional(Sequence([Singleton('e1'), Singleton('e2')])))

        pattern_dfg_f = PatternDfg()
        pattern_dfg_f.add_node('f')
        dfg.add_pattern('F', Clustering([SubGraph(pattern_dfg_f, ['f'], ['f'])],
                                         {'1': 0, '2': 0}))

        pattern_dfg_g = PatternDfg()
        pattern_dfg_g.add_node('g')
        pattern_dfg_g.add_pattern('g', Sequence.from_activity_list(['g1', 'g2']))
        dfg.add_pattern('G', SubGraph(pattern_dfg_g, ['g'], ['g']))

        expected_graph = PatternDfg()
        for edge in dfg.get_edges():
            expected_graph.add_count(edge.start.activity, edge.end.activity)
        expected_graph.add_pattern('A', Singleton('a'))
        expected_graph.add_pattern('B', Singleton('b'))
        expected_graph.add_pattern('C', Optional(Singleton('c')))
        expected_graph.add_pattern('D', Optional(Singleton('d')))
        expected_graph.add_pattern('E', Optional(Sequence([Singleton('e1'), Singleton('e2')])))
        expected_graph.add_pattern('F', Singleton('f'))
        expected_graph.add_pattern('G', Sequence.from_activity_list(['g1', 'g2']))

        dfg.remove_degenerated_patterns()

        self.assertEqual(expected_graph.get_nr_of_nodes(), dfg.get_nr_of_nodes())
        self.assertEqual(expected_graph.get_nr_of_edges(), dfg.get_nr_of_edges())
        for node in expected_graph.get_nodes():
            self.assertEqual(node.pattern, dfg.nodes[node.pattern.get_activity_name()].pattern)

    def test_convert_to_petri_net_singletons_only(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B')
        dfg.add_count('A', 'C')
        dfg.add_count('B', 'D')
        dfg.add_count('C', 'E')
        dfg.add_count('D', 'D')
        dfg.add_count('D', 'E')

        expected_petri_net = DataPetriNet()

        pre_A = expected_petri_net.add_place(Place.with_empty_label('__pre__A'))
        post_A = expected_petri_net.add_place(Place.with_empty_label('__post__A'))
        pre_B = expected_petri_net.add_place(Place.with_empty_label('__pre__B'))
        post_B = expected_petri_net.add_place(Place.with_empty_label('__post__B'))
        pre_C = expected_petri_net.add_place(Place.with_empty_label('__pre__C'))
        post_C = expected_petri_net.add_place(Place.with_empty_label('__post__C'))
        pre_D = expected_petri_net.add_place(Place.with_empty_label('__pre__D'))
        post_D = expected_petri_net.add_place(Place.with_empty_label('__post__D'))
        pre_E = expected_petri_net.add_place(Place.with_empty_label('__pre__E'))
        post_E = expected_petri_net.add_place(Place.with_empty_label('__post__E'))

        A = expected_petri_net.add_transition(Transition('A'))
        B = expected_petri_net.add_transition(Transition('B'))
        C = expected_petri_net.add_transition(Transition('C'))
        D = expected_petri_net.add_transition(Transition('D'))
        E = expected_petri_net.add_transition(Transition('E'))

        expected_petri_net.add_connection(pre_A, A, post_A)
        expected_petri_net.add_connection(pre_B, B, post_B)
        expected_petri_net.add_connection(pre_C, C, post_C)
        expected_petri_net.add_connection(pre_D, D, post_D)
        expected_petri_net.add_connection(pre_E, E, post_E)

        AB = expected_petri_net.add_transition(Transition('A->B', visible=False))
        AC = expected_petri_net.add_transition(Transition('A->C', visible=False))
        BD = expected_petri_net.add_transition(Transition('B->D', visible=False))
        CE = expected_petri_net.add_transition(Transition('C->E', visible=False))
        DD = expected_petri_net.add_transition(Transition('D->D', visible=False))
        DE = expected_petri_net.add_transition(Transition('D->E', visible=False))

        expected_petri_net.add_connection(post_A, AB, pre_B)
        expected_petri_net.add_connection(post_A, AC, pre_C)
        expected_petri_net.add_connection(post_B, BD, pre_D)
        expected_petri_net.add_connection(post_C, CE, pre_E)
        expected_petri_net.add_connection(post_D, DD, pre_D)
        expected_petri_net.add_connection(post_D, DE, pre_E)
        expected_petri_net.prune()

        self.assertEqual(dfg.convert_to_petri_net().plot(view=False),
                         expected_petri_net.plot(view=False))

    def test_get_coverable_activities(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B')
        dfg.add_count('A', 'C')
        dfg.add_count('B', 'D')
        dfg.add_count('C', 'E')
        dfg.add_count('D', 'D')
        dfg.add_count('D', 'E')

        self.assertSetEqual(set(['B', 'C']), dfg.get_coverable_activities('A'))
        self.assertSetEqual(set(['D']), dfg.get_coverable_activities('B'))
        self.assertSetEqual(set(['D', 'E']), dfg.get_coverable_activities('D'))
        self.assertSetEqual(set(), dfg.get_coverable_activities('E'))

if __name__ == '__main__':
    unittest.main()