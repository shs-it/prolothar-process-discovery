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
from prolothar_process_discovery.discovery.proseqo.pattern.loop import Loop
from prolothar_process_discovery.discovery.proseqo.pattern.blob import Blob
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.pattern.parallel import Parallel
from prolothar_process_discovery.discovery.proseqo.pattern.inclusive_choice import InclusiveChoice
from prolothar_process_discovery.discovery.proseqo.pattern.clustering import Clustering
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score
from prolothar_common.models.eventlog import EventLog

from prolothar_process_discovery.data.synthetic_baking import baking

class TestMdlScore(unittest.TestCase):

    def setUp(self):
        simple_activity_log = []
        for _ in range(200):
            simple_activity_log.append(['0','1','2','4','5','4','5','1','2','6'])
            simple_activity_log.append(['0','1','2','4','5','4','5','4','5','1','2','6'])
            simple_activity_log.append(['0','1','2','4','5','1','2','6'])
            simple_activity_log.append(['0','7','8','6'])
        for _ in range(1):
            simple_activity_log.append(['0','7','8','2','6'])
        self.event_log_with_sequence_patterns = EventLog.create_from_simple_activity_log(
                simple_activity_log)

    def test_compute_mdl_score(self):
        dfg_without_patterns = PatternDfg.create_from_event_log(
                self.event_log_with_sequence_patterns)

        dfg_with_missing_edges = PatternDfg()
        dfg_with_missing_edges.add_count('0', '1')
        dfg_with_missing_edges.add_count('0', '7')
        dfg_with_missing_edges.add_count('2', '4')
        dfg_with_missing_edges.add_count('2', '6')
        dfg_with_missing_edges.add_count('5', '1')
        dfg_with_missing_edges.add_count('5', '4')
        dfg_with_missing_edges.add_count('7', '8')
        dfg_with_missing_edges.add_count('8', '6')

        dfg_with_patterns = dfg_without_patterns.fold({
                Sequence([Singleton('1'), Singleton('2')]),
                Sequence([Singleton('4'), Singleton('5')]),
                Sequence([Singleton('7'), Singleton('8')]),
        })

        dfg_with_bad_patterns = PatternDfg()
        dfg_with_bad_patterns.add_count('0', '[1,5]')
        dfg_with_bad_patterns.add_count('0', '7')
        dfg_with_bad_patterns.add_count('[1,5]', '[2,8]')
        dfg_with_bad_patterns.add_count('[2,8]', '[1,5]')
        dfg_with_bad_patterns.add_count('[2,8]', '6')
        dfg_with_bad_patterns.add_pattern('[1,5]', Sequence.from_activity_list(['1','5']))
        dfg_with_bad_patterns.add_pattern('[2,8]', Sequence.from_activity_list(['2','8']))

        dfg_with_noise_removed = dfg_without_patterns.copy()
        dfg_with_noise_removed.remove_edge(('8', '2'))

        mdl_score_without_patterns = compute_mdl_score(
                self.event_log_with_sequence_patterns, dfg_without_patterns,
                verbose=False)
        mdl_score_with_missing_edges = compute_mdl_score(
                self.event_log_with_sequence_patterns, dfg_with_missing_edges)
        mdl_score_with_patterns = compute_mdl_score(
                self.event_log_with_sequence_patterns, dfg_with_patterns,
                verbose=False)
        mdl_score_with_bad_patterns = compute_mdl_score(
                self.event_log_with_sequence_patterns, dfg_with_bad_patterns)
        mdl_score_with_noise_removed = compute_mdl_score(
                self.event_log_with_sequence_patterns, dfg_with_noise_removed,
                verbose=False)
        self.assertLess(mdl_score_with_noise_removed, mdl_score_without_patterns)
        self.assertLess(mdl_score_with_patterns, mdl_score_without_patterns)
        self.assertLess(mdl_score_with_patterns, mdl_score_with_missing_edges)
        self.assertLess(mdl_score_with_patterns, mdl_score_with_bad_patterns)
        self.assertLess(mdl_score_without_patterns, mdl_score_with_bad_patterns)

    def test_compute_mdl_score_community_folden_dfg(self):
        community_1_2 = PatternDfg()
        community_1_2.add_count('1', '2')
        community_1_2 = SubGraph(community_1_2, ['1'], ['2'])

        community_4_5 = PatternDfg()
        community_4_5.add_count('4', '5')
        community_4_5 = SubGraph(community_4_5, ['4'], ['5'])

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('0', '1,2')
        dfg_with_patterns.add_count('[{1},...,{2}]', '[{4},...,{5}]')
        dfg_with_patterns.add_count('[{1},...,{2}]', '6')
        dfg_with_patterns.add_count('[{4},...,{5}]', '[{1},...,{2}]')
        dfg_with_patterns.add_count('[{4},...,{5}]', '[{4},...,{5}]')
        dfg_with_patterns.add_pattern('[{1},...,{2}]', community_1_2)
        dfg_with_patterns.add_pattern('[{4},...,{5}]', community_4_5)

        compute_mdl_score(self.event_log_with_sequence_patterns,
                          dfg_with_patterns)

    def test_compute_mdl_score_nested_community_folden_dfg(self):
        simple_activity_log = []
        for _ in range(50):
            simple_activity_log.append(['0','1','2','4','6','7'])
            simple_activity_log.append(['0','1','2','3','5','4','6','7'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg_without_patterns = PatternDfg.create_from_event_log(log)

        community = PatternDfg()
        community.add_count('2', '[3,5]')
        community.add_count('2', '4')
        community.add_count('[3,5]', '4')
        community.add_pattern('[3,5]', Sequence.from_activity_list(['3', '5']))
        community = SubGraph(community, ['2'], ['4'])

        dfg_with_patterns = dfg_without_patterns.fold({community})

        compute_mdl_score(
                log, dfg_with_patterns, verbose=False)

    def test_compute_mdl_score_with_sequence_and_optional(self):
        simple_activity_log = []
        for _ in range(50):
            simple_activity_log.append(['0','1','2','4','6','7'])
            simple_activity_log.append(['0','1','2','3','5','4','6','7'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg_without_patterns = PatternDfg.create_from_event_log(log)

        dfg_with_patterns = dfg_without_patterns.fold({Sequence([
            Singleton('0'), Singleton('1'), Singleton('2'),
            Optional(Sequence.from_activity_list(['3', '5']))]),
            Singleton('4'), Singleton('6'), Singleton('7')
        })

        mdl_score_without_patterns = compute_mdl_score(
                log, dfg_without_patterns, verbose=False)
        mdl_score_with_patterns = compute_mdl_score(
                log, dfg_with_patterns, verbose=False)
        self.assertLess(mdl_score_with_patterns, mdl_score_without_patterns)

    def test_optional_with_multi_connections_should_decrease_mdl_score(self):
        simple_activity_log = []
        for _ in range(50):
            simple_activity_log.append(['0.0','1','2.0'])
            simple_activity_log.append(['0.0','1','2.1'])
            simple_activity_log.append(['0.0','2.0'])
            simple_activity_log.append(['0.0','2.1'])
            simple_activity_log.append(['0.1','2.0'])
            simple_activity_log.append(['0.1','2.1'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg_without_patterns = PatternDfg.create_from_event_log(log)

        dfg_with_patterns = dfg_without_patterns.fold({
            Optional(Singleton('1'))
        })

        mdl_score_without_patterns = compute_mdl_score(
                log, dfg_without_patterns, verbose=False)
        mdl_score_with_patterns = compute_mdl_score(
                log, dfg_with_patterns, verbose=False)
        self.assertLess(mdl_score_with_patterns, mdl_score_without_patterns)

    def test_loop_should_not_increase_mdl_score(self):
        dfg = PatternDfg()
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'B')
        dfg.add_count('B', 'C')
        folded_dfg = dfg.fold({Loop(Singleton('B'))})

        simple_activity_log = []
        for _ in range(50):
            simple_activity_log.append(['A','B','B','B','C'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        mdl_score_without_loop = compute_mdl_score(log, dfg, verbose=False)
        mdl_score_with_loop = compute_mdl_score(log, folded_dfg, verbose=False)

        self.assertLess(mdl_score_with_loop, mdl_score_without_loop)

    def test_parallel_should_be_able_to_decrase_mdl(self):
        dfg = PatternDfg()
        dfg.add_count('0', 'A')
        dfg.add_count('0', 'B')
        dfg.add_count('0', 'C')
        dfg.add_count('A', 'B')
        dfg.add_count('B', 'A')
        dfg.add_count('B', 'C')
        dfg.add_count('C', 'A')
        dfg.add_count('A', '1')
        dfg.add_count('C', '1')

        folded_dfg = dfg.fold({Parallel.from_activity_list(['A','B','C'])})

        simple_activity_log = []
        for _ in range(10):
            simple_activity_log.append(['0','A','B','C','1'])
            simple_activity_log.append(['0','C','A','B','1'])
            simple_activity_log.append(['0','B','C','A','1'])
            simple_activity_log.append(['0','A','C','B','1'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        mdl_score_without_pattern = compute_mdl_score(log, dfg, verbose=False)
        mdl_score_with_pattern = compute_mdl_score(log, folded_dfg, verbose=False)

        self.assertLess(mdl_score_with_pattern, mdl_score_without_pattern)

    def test_good_models_should_lead_to_smaller_mdl(self):
        log = baking.generate_log(100, use_clustering_model=True)

        dfg = PatternDfg.create_from_event_log(log)

        mdl_complete_dfg = compute_mdl_score(log, dfg, verbose=False)

        good_model = dfg.fold({Sequence([
                Singleton('Take out of the Oven'),
                Optional(Singleton('Sprinkle with Icing Sugar')),
                Singleton('Eat'),
                Singleton('Smile'),
                Singleton('End')])
        })
        mdl_good_model = compute_mdl_score(log, good_model, verbose=False)

        optimal_model = baking.get_ideal_pattern_graph_with_clustering(log)
        mdl_optimal_model = compute_mdl_score(log, optimal_model)
        self.assertGreater(mdl_optimal_model, 0)

        empty_DFG = PatternDfg()
        empty_DFG.add_count('Start', 'End')
        mdl_empty_dfg = compute_mdl_score(log, empty_DFG)

        mdl_list = [mdl_optimal_model, mdl_good_model, mdl_complete_dfg, mdl_empty_dfg]
        self.assertListEqual(mdl_list, sorted(mdl_list))

    def test_choice_with_partial_observations_should_still_be_able_to_decrease_mdl(self):
        simple_activity_log = []
        for _ in range(4):
            simple_activity_log.append(['0', 'A1','B1'])
            simple_activity_log.append(['0', 'A1','B2'])
            simple_activity_log.append(['0', 'A2','B1'])
            simple_activity_log.append(['0', 'A2','B2'])
            simple_activity_log.append(['0', 'A2','B3'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg_without_patterns = PatternDfg.create_from_event_log(log)

        dfg_with_patterns = dfg_without_patterns.fold({Sequence([
                Choice([Singleton('A1'), Singleton('A2')]),
                Choice([Singleton('B1'), Singleton('B2'), Singleton('B3')])
            ])})

        mdl_score_without_patterns = compute_mdl_score(
                log, dfg_without_patterns, verbose=False)

        mdl_score_with_patterns = compute_mdl_score(
                log, dfg_with_patterns, verbose=False)
        self.assertLess(mdl_score_with_patterns, mdl_score_without_patterns)

    def test_clustering_should_decrease_mdl(self):
        simple_activity_log = []
        for _ in range(50):
            simple_activity_log.append(['A', '1', '2', 'E'])
            simple_activity_log.append(['A', '1', '3', 'E'])
            simple_activity_log.append(['A', '2', '3', 'E'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        trace_cluster_dict = {}
        for i,trace in enumerate(log.traces):
            trace_cluster_dict[trace] = i % 3

        dfg_without_patterns = PatternDfg.create_from_event_log(log)

        cluster1 = Sequence.from_activity_list(['1', '2'])
        cluster2 = Sequence.from_activity_list(['1', '3'])
        cluster3 = Sequence.from_activity_list(['2', '3'])
        cluster_pattern = Clustering([cluster1, cluster2, cluster3],
                                     trace_cluster_dict)
        folded_dfg = dfg_without_patterns.fold({cluster_pattern})

        mdl_score_without_patterns = compute_mdl_score(
                log, dfg_without_patterns, verbose=False)
        mdl_score_with_patterns = compute_mdl_score(
                log, folded_dfg, verbose=False)
        self.assertLess(mdl_score_with_patterns, mdl_score_without_patterns)

    def test_small_perfect_sequence_should_lead_to_best_mdl(self):
        simple_activity_log = []
        for _ in range(100):
            simple_activity_log.append(['A', 'B'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg = PatternDfg.create_from_event_log(log)

        pdfg = dfg.fold({Sequence.from_activity_list(['A', 'B'])})

        dfg_mdl = compute_mdl_score(log, dfg, verbose=False)

        pdfg_mdl = compute_mdl_score(log, pdfg, verbose=False)
        self.assertLess(pdfg_mdl, dfg_mdl)

    def test_small_perfect_choice_should_lead_to_best_mdl(self):
        simple_activity_log = []
        for _ in range(20):
            simple_activity_log.append(['A', 'B', 'D'])
        for _ in range(10):
            simple_activity_log.append(['A', 'C', 'D'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg = PatternDfg.create_from_event_log(log)

        pdfg = dfg.fold({Choice([Singleton('B'), Singleton('C')])})

        dfg_mdl = compute_mdl_score(log, dfg, verbose=False)
        pdfg_mdl = compute_mdl_score(log, pdfg, verbose=False)
        self.assertLess(pdfg_mdl, dfg_mdl)

    def test_small_perfect_choice_with_sequences_should_lead_to_best_mdl(self):
        simple_activity_log = []
        for _ in range(20):
            simple_activity_log.append(['A', 'B1', 'B2', 'D'])
        for _ in range(10):
            simple_activity_log.append(['A', 'C1', 'C2', 'D'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg = PatternDfg.create_from_event_log(log)

        dfg_with_sequences = dfg.fold({Sequence.from_activity_list(['B1', 'B2']),
                                       Sequence.from_activity_list(['C1', 'C2'])})

        dfg_with_choice = dfg_with_sequences.fold({Choice([
                Sequence.from_activity_list(['B1', 'B2']),
                Sequence.from_activity_list(['C1', 'C2'])
        ])})

        dfg_mdl = compute_mdl_score(log, dfg, verbose=False)
        dfg_with_sequences_mdl = compute_mdl_score(log, dfg_with_sequences, verbose=False)
        dfg_with_choice_mdl = compute_mdl_score(log, dfg_with_choice, verbose=False)
        self.assertLess(dfg_with_sequences_mdl, dfg_mdl)
        self.assertLess(dfg_with_choice_mdl, dfg_with_sequences_mdl)

    def test_redundant_clustering_should_not_decrease_mdl(self):
        simple_activity_log = []
        for _ in range(50):
            simple_activity_log.append(['A', '1', '2', 'E'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        trace_cluster_dict = {}
        for i,trace in enumerate(log.traces):
            trace_cluster_dict[trace] = i % 2

        dfg_without_clustering = PatternDfg.create_from_event_log(log).fold({
                Sequence.from_activity_list(['1', '2'])})

        cluster1 = Sequence.from_activity_list(['1', '2'])
        cluster2 = Sequence.from_activity_list(['1', '2'])
        cluster_pattern = Clustering([cluster1, cluster2], trace_cluster_dict)
        folded_dfg = PatternDfg.create_from_event_log(log).fold({cluster_pattern})

        mdl_score_without_patterns = compute_mdl_score(
                log, dfg_without_clustering, verbose=False)
        mdl_score_with_patterns = compute_mdl_score(
                log, folded_dfg, verbose=False)
        self.assertLess(mdl_score_without_patterns, mdl_score_with_patterns)


    def test_choice_of_two_sequences(self):
        simple_activity_log = []
        for _ in range(50):
            simple_activity_log.append(['0', 'A', 'B', '1'])
            simple_activity_log.append(['0', 'C', 'D', '1'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg = PatternDfg.create_from_event_log(log)
        dfg_mdl = compute_mdl_score(log, dfg, verbose=False)

        dfg_choice_of_sequences = dfg.fold({
                Choice([Sequence.from_activity_list(['A', 'B']),
                        Sequence.from_activity_list(['C', 'D'])])
        })
        dfg_choice_of_sequences_mdl = compute_mdl_score(
                log, dfg_choice_of_sequences, verbose=False)

        dfg_sequence_of_choices = dfg.fold({
                Sequence([Choice([Singleton('A'), Singleton('B')]),
                          Choice([Singleton('C'), Singleton('D')])])
        })
        dfg_sequence_of_choices_mdl = compute_mdl_score(
                log, dfg_sequence_of_choices)

        self.assertLess(dfg_choice_of_sequences_mdl, dfg_mdl)
        self.assertLess(dfg_choice_of_sequences_mdl, dfg_sequence_of_choices_mdl)

    def test_blob_should_be_able_to_decrease_mdl(self):
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
        dfg.add_count('h', 'e')

        #non-blob to blob
        dfg.add_count('c', 'k')
        dfg.add_count('c', 'g')
        dfg.add_count('c', 'h')

        log = dfg.generate_log(100, random_seed=42)

        mdl_dfg = compute_mdl_score(log, dfg, verbose=False)

        dfg_with_blob = dfg.fold({
            Blob({'g', 'h', 'k', 'l'})
        })
        mdl_with_blob = compute_mdl_score(log, dfg_with_blob, verbose=False)

        self.assertLess(mdl_with_blob, mdl_dfg)

    def test_inclusive_choice_should_be_able_to_decrease_mdl(self):
        log = EventLog.create_from_simple_activity_log([
            ['0', 'A', 'B', 'C', 'D', '1'],
            ['0', 'A', 'B', 'C', 'D', '1'],
            ['0', 'A', 'B', 'C', 'D', '1'],
            ['0', 'A', 'C', 'B', '1'],
            ['0', 'A', 'C', 'B', '1'],
            ['0', 'C', 'A', 'B', '1'],
            ['0', 'A', 'C', 'D', 'A', '1'],
            ['0', 'A', 'C', 'D', 'A', '1'],
        ])
        dfg = PatternDfg.create_from_event_log(log)
        mdl_dfg = compute_mdl_score(log, dfg, verbose=False)

        choice = InclusiveChoice([Singleton('A'),
                                  Singleton('B'),
                                  Singleton('C'),
                                  Singleton('D')])

        dfg_with_choice = dfg.fold({choice})
        mdl_with_choice = compute_mdl_score(log, dfg_with_choice, verbose=False)

        self.assertLess(mdl_with_choice, mdl_dfg)

    def test_removal_of_a_should_not_decrease_mdl(self):
        log = []
        for i in range(50):
            log.append(['START', 'a', 'f', 'g', 'END'])
            log.append(['START', 'a', 'c', 'e', 'd', 'i', 'h', 'END'])
            log.append(['START', 'a', 'b', 'END'])
        log = EventLog.create_from_simple_activity_log(log)

        dfg = PatternDfg.create_from_event_log(log)
        mdl_dfg = compute_mdl_score(log, dfg, verbose=False)

        dfg_without_a = dfg.copy()
        dfg_without_a.remove_node('a')
        dfg_without_a_mdl = compute_mdl_score(log, dfg_without_a, verbose=False)

        self.assertLess(mdl_dfg, dfg_without_a_mdl)

    def test_partial_explaining_patterns_should_make_sense(self):
        log = []
        for i in range(50):
            log.append(['START', 'a', 'f', 'g', 'END'])
            log.append(['START', 'a', 'c', 'e', 'd', 'i', 'h', 'END'])
            log.append(['START', 'a', 'b', 'END'])
        log = EventLog.create_from_simple_activity_log(log)

        pattern_dfg_a = PatternDfg.of_pattern(Sequence([
                Singleton('START'),
                Singleton('a'),
                Optional(Singleton('f')),
                Singleton('END')
        ]))
        pattern_dfg_b = PatternDfg.of_pattern(Sequence([
                Optional(Singleton('f')),
                Singleton('START'),
                Singleton('a'),
                Singleton('END')
        ]))

        mdl_a = compute_mdl_score(log, pattern_dfg_a, verbose=False)
        mdl_b = compute_mdl_score(log, pattern_dfg_b, verbose=False)

        self.assertLess(mdl_a, mdl_b)

    def test_partial_explaining_patterns_should_make_sense_2(self):
        log = []
        for i in range(50):
            log.append(['START', 'a', 'f', 'g', 'END'])
            log.append(['START', 'a', 'c', 'e', 'd', 'i', 'h', 'END'])
            log.append(['START', 'a', 'b', 'END'])
        log = EventLog.create_from_simple_activity_log(log)
        pattern_dfg_a = PatternDfg.of_pattern(Sequence([
                Singleton('START'),
                Singleton('a'),
                Optional(Sequence([
                        Singleton('f'),
                        Singleton('g'),
                ])),
                Singleton('END')
        ]))
        pattern_dfg_b = PatternDfg.of_pattern(Sequence([
                Optional(Singleton('c')),
                Singleton('START'),
                Singleton('a'),
                Optional(Sequence([
                        Singleton('f'),
                        Singleton('g'),
                ])),
                Singleton('END')
        ]))

        mdl_a = compute_mdl_score(log, pattern_dfg_a, verbose=False)
        mdl_b = compute_mdl_score(log, pattern_dfg_b, verbose=False)

        self.assertLess(mdl_a, mdl_b)

    def test_should_be_able_to_find_perfect_pattern_representation_2(self):
        log = []
        for i in range(10):
            log.append(['START', 'a', 'c', 'h', 'b', 'e', 'd', 'j', 'END'])
            log.append(['START', 'f', 'c', 'h', 'b', 'e', 'd', 'j', 'END'])
            log.append(['START', 'f', 'c', 'h', 'b', 'e', 'g', 'i', 'END'])
        log = EventLog.create_from_simple_activity_log(log)

        pattern_dfg_a = PatternDfg.of_pattern(Sequence([
            Singleton('START'),
            Choice([
                Singleton('a'),
                Singleton('f')
            ]),
            Singleton('c'),
            Singleton('h'),
            Singleton('b'),
            Singleton('e'),
            Choice([
                Sequence.from_activity_list(['d', 'j']),
                Sequence.from_activity_list(['g', 'i']),
            ]),
            Singleton('END')
        ]))

        pattern_dfg_b = PatternDfg.of_pattern(Sequence([
            Singleton('START'),
            Optional(Singleton('f')),
            Singleton('c'),
            Singleton('h'),
            Singleton('b'),
            Singleton('e'),
            Choice([
                Sequence.from_activity_list(['d', 'j']),
                Sequence.from_activity_list(['g', 'i']),
            ]),
            Singleton('END')
        ]))

        mdl_a = compute_mdl_score(log, pattern_dfg_a, verbose=False)
        print('....')
        mdl_b = compute_mdl_score(log, pattern_dfg_b, verbose=False)
        print('....')

        self.assertLess(mdl_a, mdl_b)

    def test_true_model_should_be_cheaper_than_dfg(self):
        true_model = PatternDfg.of_pattern(Sequence([
            Singleton('START'),
            Choice([
                Sequence([
                    Loop(Sequence([
                        Singleton('b'),
                        Choice([
                            Sequence.from_activity_list(['p', 'v']),
                            Singleton('k')
                        ]),
                        Choice([
                            Sequence.from_activity_list(['n', 'o']),
                            Singleton('i')
                        ]),
                        Optional(Choice([
                            Singleton('c'),
                            Singleton('j')
                        ]))
                    ])),
                    Loop(Sequence([
                        Optional(Sequence([
                            Choice([
                                Sequence.from_activity_list(['r', 'w']),
                                Singleton('d')
                            ]),
                            Choice([
                                Singleton('m'),
                                Singleton('y')
                            ])
                        ])),
                        Optional(Sequence.from_activity_list(['e', 'u', 'x']))
                    ])),
                    Singleton('f')
                ]),
                Sequence([
                    Singleton('a'),
                    Choice([
                        Sequence([
                            Loop(Singleton('g')),
                            Singleton('s'),
                            Singleton('q')
                        ]),
                        Sequence.from_activity_list(['h', 't', 'l'])
                    ])
                ])
            ]),
            Singleton('END')
        ]))
        log = true_model.generate_log(1000, random_seed=42)
        dfg = PatternDfg.create_from_event_log(log)

        mdl_true_model = compute_mdl_score(log, true_model)
        mdl_dfg = compute_mdl_score(log, dfg)

        self.assertLess(mdl_true_model, mdl_dfg)

    def test_true_model_should_be_cheaper_than_intermediate_result(self):
        true_model = PatternDfg.of_pattern(Sequence([
            Singleton('START'),
            Choice([
                Sequence([
                    Loop(Sequence([
                        Singleton('b'),
                        Choice([
                            Sequence.from_activity_list(['p', 'v']),
                            Singleton('k')
                        ]),
                        Choice([
                            Sequence.from_activity_list(['n', 'o']),
                            Singleton('i')
                        ]),
                        Optional(Choice([
                            Singleton('c'),
                            Singleton('j')
                        ]))
                    ])),
                    Loop(Sequence([
                        Optional(Sequence([
                            Choice([
                                Sequence.from_activity_list(['r', 'w']),
                                Singleton('d')
                            ]),
                            Choice([
                                Singleton('m'),
                                Singleton('y')
                            ])
                        ])),
                        Optional(Sequence.from_activity_list(['e', 'u', 'x']))
                    ])),
                    Singleton('f')
                ]),
                Sequence([
                    Singleton('a'),
                    Choice([
                        Sequence([
                            Loop(Singleton('g')),
                            Singleton('s'),
                            Singleton('q')
                        ]),
                        Sequence.from_activity_list(['h', 't', 'l'])
                    ])
                ])
            ]),
            Singleton('END')
        ]))
        log = true_model.generate_log(1000, random_seed=42)

        intermediate_result = PatternDfg()

        pattern_1 = Loop(Sequence([
            Singleton('b'),
            Choice([
                Sequence.from_activity_list(['p', 'v']),
                Singleton('k'),
            ]),
            Choice([
                Sequence.from_activity_list(['n', 'o']),
                Singleton('i'),
            ]),
            Optional(Choice([
                Singleton('c'),
                Singleton('j')
            ]))
        ]))
        intermediate_result.add_node(pattern_1.get_activity_name())
        intermediate_result.add_pattern(
                pattern_1.get_activity_name(), pattern_1)

        pattern_2 = Choice([Singleton('m'), Singleton('y')])
        intermediate_result.add_node(pattern_2.get_activity_name())
        intermediate_result.add_pattern(
                pattern_2.get_activity_name(), pattern_2)

        pattern_3 = Sequence.from_activity_list(['e', 'u', 'x'])
        intermediate_result.add_node(pattern_3.get_activity_name())
        intermediate_result.add_pattern(
                pattern_3.get_activity_name(), pattern_3)

        pattern_4 = Sequence.from_activity_list(['r', 'w'])
        intermediate_result.add_node(pattern_4.get_activity_name())
        intermediate_result.add_pattern(
                pattern_4.get_activity_name(), pattern_4)

        pattern_5 = Sequence([
            Singleton('a'),
            Choice([
                Sequence([
                    Loop(Singleton('g')),
                    Singleton('s'),
                    Singleton('q')
                ]),
                Sequence.from_activity_list(['h', 't', 'l'])
            ])
        ])
        intermediate_result.add_node(pattern_5.get_activity_name())
        intermediate_result.add_pattern(
                pattern_5.get_activity_name(), pattern_5)

        intermediate_result.add_count('START', pattern_1.get_activity_name())
        intermediate_result.add_count('START', pattern_5.get_activity_name())
        intermediate_result.add_count(pattern_1.get_activity_name(), 'd')
        intermediate_result.add_count(pattern_1.get_activity_name(), 'f')
        intermediate_result.add_count(pattern_1.get_activity_name(),
                                      pattern_3.get_activity_name())
        intermediate_result.add_count(pattern_1.get_activity_name(),
                                      pattern_4.get_activity_name())
        intermediate_result.add_count(pattern_2.get_activity_name(), 'f')
        intermediate_result.add_count(pattern_2.get_activity_name(),
                                      pattern_3.get_activity_name())
        intermediate_result.add_count(pattern_2.get_activity_name(),
                                      pattern_4.get_activity_name())
        intermediate_result.add_count(pattern_2.get_activity_name(), 'd')
        intermediate_result.add_count(pattern_1.get_activity_name(),
                                      pattern_4.get_activity_name())
        intermediate_result.add_count(pattern_5.get_activity_name(), 'END')
        intermediate_result.add_count(pattern_3.get_activity_name(),
                                      pattern_3.get_activity_name())
        intermediate_result.add_count(pattern_3.get_activity_name(), 'f')
        intermediate_result.add_count(pattern_3.get_activity_name(), 'd')
        intermediate_result.add_count(pattern_3.get_activity_name(),
                                      pattern_4.get_activity_name())
        intermediate_result.add_count('f', 'END')
        intermediate_result.add_count('d', pattern_2.get_activity_name())
        intermediate_result.add_count(pattern_4.get_activity_name(),
                                      pattern_2.get_activity_name())

        mdl_true_model = compute_mdl_score(log, true_model)
        mdl_intermediate_result = compute_mdl_score(log, intermediate_result,
                                                    verbose=True)

        self.assertLess(mdl_true_model, mdl_intermediate_result)

    def test_rarely_absent_optional_vs_edge_removal(self):
        log = []
        for i in range(100):
            log.append(['START', 'a', 'END'])
        log.append(['START', 'END'])
        log = EventLog.create_from_simple_activity_log(log)

        dfg = PatternDfg.create_from_event_log(log)
        cleaned_dfg = dfg.copy()
        cleaned_dfg.remove_edge(('START', 'END'))
        optional_dfg = dfg.fold({
            Optional(Singleton('a'))
        })

        mdl_dfg = compute_mdl_score(log, dfg, verbose=False)
        mdl_cleaned_dfg = compute_mdl_score(log, cleaned_dfg,
                                            verbose=False)
        mdl_optional_dfg = compute_mdl_score(log, optional_dfg,
                                             verbose=False)

        self.assertLess(mdl_cleaned_dfg, mdl_dfg)
        self.assertLess(mdl_cleaned_dfg, mdl_optional_dfg)

if __name__ == '__main__':
    unittest.main()