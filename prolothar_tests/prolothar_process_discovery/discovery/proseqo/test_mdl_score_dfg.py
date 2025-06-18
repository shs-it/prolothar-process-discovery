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
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.pattern.parallel import Parallel
from prolothar_process_discovery.discovery.proseqo.mdl_score_dfg import compute_mdl_score_dfg
from prolothar_common.models.eventlog import EventLog

from prolothar_process_discovery.data.synthetic_baking import baking

class TestMdlScoreDfg(unittest.TestCase):

    def setUp(self):
        simple_activity_log = []
        for _ in range(20):
            simple_activity_log.append(['0','1','2','4','5','4','5','1','2','6'])
            simple_activity_log.append(['0','1','2','4','5','4','5','4','5','1','2','6'])
            simple_activity_log.append(['0','1','2','4','5','1','2','6'])
            simple_activity_log.append(['0','7','8','6'])
        simple_activity_log.append(['0','7','8','2','6'])
        self.dfg_of_log_with_sequence_patterns = PatternDfg.create_from_event_log(
                EventLog.create_from_simple_activity_log(simple_activity_log))

    def test_compute_mdl_score(self):
        dfg_without_patterns = PatternDfg()
        dfg_without_patterns.add_count('0', '1')
        dfg_without_patterns.add_count('0', '7')
        dfg_without_patterns.add_count('1', '2')
        dfg_without_patterns.add_count('2', '4')
        dfg_without_patterns.add_count('2', '6')
        dfg_without_patterns.add_count('4', '5')
        dfg_without_patterns.add_count('5', '1')
        dfg_without_patterns.add_count('5', '4')
        dfg_without_patterns.add_count('7', '8')
        dfg_without_patterns.add_count('8', '6')
        dfg_without_patterns.add_count('8', '2')

        dfg_with_missing_edges = PatternDfg()
        dfg_with_missing_edges.add_count('0', '1')
        dfg_with_missing_edges.add_count('0', '7')
        dfg_with_missing_edges.add_count('2', '4')
        dfg_with_missing_edges.add_count('2', '6')
        dfg_with_missing_edges.add_count('5', '1')
        dfg_with_missing_edges.add_count('5', '4')
        dfg_with_missing_edges.add_count('7', '8')
        dfg_with_missing_edges.add_count('8', '6')

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('0', '[1,2]')
        dfg_with_patterns.add_count('0', '[7,8]')
        dfg_with_patterns.add_count('[1,2]', '[4,5]')
        dfg_with_patterns.add_count('[1,2]', '6')
        dfg_with_patterns.add_count('[4,5]', '[1,2]')
        dfg_with_patterns.add_count('[4,5]', '[4,5]')
        dfg_with_patterns.add_count('[7,8]', '6')
        dfg_with_patterns.add_pattern('[1,2]', Sequence([Singleton('1'),
                                                         Singleton('2')]))
        dfg_with_patterns.add_pattern('[4,5]', Sequence([Singleton('4'),
                                                         Singleton('5')]))
        dfg_with_patterns.add_pattern('[7,8]', Sequence([Singleton('7'),
                                                         Singleton('8')]))

        dfg_with_bad_patterns = PatternDfg()
        dfg_with_bad_patterns.add_count('0', '[1,5]')
        dfg_with_bad_patterns.add_count('0', '7')
        dfg_with_bad_patterns.add_count('[1,5]', '[2,8]')
        dfg_with_bad_patterns.add_count('[2,8]', '[1,5]')
        dfg_with_bad_patterns.add_count('[2,8]', '6')
        dfg_with_bad_patterns.add_pattern('[1,5]', Sequence.from_activity_list(['1','5']))
        dfg_with_bad_patterns.add_pattern('[2,8]', Sequence.from_activity_list(['2','8']))

        dfg_with_noise_removed = PatternDfg()
        dfg_with_noise_removed.add_count('0', '1')
        dfg_with_noise_removed.add_count('0', '7')
        dfg_with_noise_removed.add_count('1', '2')
        dfg_with_noise_removed.add_count('2', '4')
        dfg_with_noise_removed.add_count('2', '6')
        dfg_with_noise_removed.add_count('4', '5')
        dfg_with_noise_removed.add_count('5', '1')
        dfg_with_noise_removed.add_count('5', '4')
        dfg_with_noise_removed.add_count('7', '8')
        dfg_with_noise_removed.add_count('8', '6')

        mdl_score_without_patterns = compute_mdl_score_dfg(
                self.dfg_of_log_with_sequence_patterns, dfg_without_patterns,
                verbose=False)
        mdl_score_with_missing_edges = compute_mdl_score_dfg(
                self.dfg_of_log_with_sequence_patterns, dfg_with_missing_edges)
        mdl_score_with_patterns = compute_mdl_score_dfg(
                self.dfg_of_log_with_sequence_patterns, dfg_with_patterns,
                verbose=False)
        mdl_score_with_bad_patterns = compute_mdl_score_dfg(
                self.dfg_of_log_with_sequence_patterns, dfg_with_bad_patterns)
        mdl_score_with_noise_removed = compute_mdl_score_dfg(
                self.dfg_of_log_with_sequence_patterns, dfg_with_noise_removed)

        self.assertLess(mdl_score_with_patterns, mdl_score_without_patterns)
        self.assertLess(mdl_score_with_patterns, mdl_score_with_missing_edges)
        self.assertLess(mdl_score_with_patterns, mdl_score_with_bad_patterns)
        self.assertLess(mdl_score_without_patterns, mdl_score_with_bad_patterns)
        self.assertLess(mdl_score_with_noise_removed, mdl_score_without_patterns)

    def test_compute_mdl_score_community_folden_dfg(self):
        community_1_2 = PatternDfg()
        community_1_2.add_count('1', '2')
        community_1_2 = SubGraph(community_1_2, ['1'], ['2'])

        community_4_5 = PatternDfg()
        community_4_5.add_count('4', '5')
        community_4_5 = SubGraph(community_4_5, ['4'], ['5'])

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('0', '1,2')
        dfg_with_patterns.add_count('1,2', '4,5')
        dfg_with_patterns.add_count('1,2', '6')
        dfg_with_patterns.add_count('4,5', '1,2')
        dfg_with_patterns.add_count('4,5', '4,5')
        dfg_with_patterns.add_pattern('1,2', community_1_2)
        dfg_with_patterns.add_pattern('4,5', community_4_5)

        compute_mdl_score_dfg(self.dfg_of_log_with_sequence_patterns,
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

        compute_mdl_score_dfg(
                dfg_without_patterns, dfg_with_patterns, verbose=False)

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
                Singleton('4'), Singleton('6'), Singleton('7')})

        mdl_score_without_patterns = compute_mdl_score_dfg(
                dfg_without_patterns, dfg_without_patterns, verbose=False)
        mdl_score_with_patterns = compute_mdl_score_dfg(
                dfg_without_patterns, dfg_with_patterns, verbose=False)
        self.assertLess(mdl_score_with_patterns, mdl_score_without_patterns)

    def test_optional_should_not_increase_mdl_score(self):
        simple_activity_log = []
        for _ in range(50):
            simple_activity_log.append(['0','1','2'])
            simple_activity_log.append(['0','2'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg_without_patterns = PatternDfg.create_from_event_log(log)

        dfg_with_patterns = dfg_without_patterns.fold({
            Optional(Singleton('1'))
        })
        mdl_score_without_patterns = compute_mdl_score_dfg(
                dfg_without_patterns, dfg_without_patterns, verbose=True)
        mdl_score_with_patterns = compute_mdl_score_dfg(
                dfg_without_patterns, dfg_with_patterns, verbose=True)
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
        dfg_of_log = PatternDfg.create_from_event_log(log)

        mdl_score_without_loop = compute_mdl_score_dfg(dfg_of_log, dfg)
        mdl_score_with_loop = compute_mdl_score_dfg(dfg_of_log, folded_dfg)

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
        dfg_of_log = PatternDfg.create_from_event_log(log)

        mdl_score_without_pattern = compute_mdl_score_dfg(dfg_of_log, dfg)
        mdl_score_with_pattern = compute_mdl_score_dfg(dfg_of_log, folded_dfg)

        self.assertLess(mdl_score_with_pattern, mdl_score_without_pattern)

    def test_good_models_should_lead_to_smaller_mdl(self):
        log = baking.generate_log(100, use_clustering_model=True)

        dfg = PatternDfg.create_from_event_log(log)

        mdl_complete_dfg = compute_mdl_score_dfg(dfg, dfg, verbose=True)

        good_model = dfg.fold({
            Sequence([
                Singleton('Take out of the Oven'),
                Optional(Singleton('Sprinkle with Icing Sugar')),
                Singleton('Eat'),
                Singleton('Smile'),
                Singleton('End')
            ])
        })
        mdl_good_model = compute_mdl_score_dfg(dfg, good_model)

        empty_DFG = PatternDfg()
        empty_DFG.add_count('Start', 'End')
        print('------------')
        mdl_empty_dfg = compute_mdl_score_dfg(dfg, empty_DFG, verbose=True)

        mdl_list = [mdl_good_model, mdl_complete_dfg, mdl_empty_dfg]
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

        dfg_with_patterns = dfg_without_patterns.fold({
            Sequence([
                Choice([Singleton('A1'), Singleton('A2')]),
                Choice([Singleton('B1'), Singleton('B2'), Singleton('B3')])
            ])
        })

        mdl_score_without_patterns = compute_mdl_score_dfg(
                dfg_without_patterns, dfg_without_patterns, verbose=False)

        mdl_score_with_patterns = compute_mdl_score_dfg(
                dfg_without_patterns, dfg_with_patterns, verbose=False)
        self.assertLess(mdl_score_with_patterns, mdl_score_without_patterns)

    def test_small_perfect_sequence_should_lead_to_best_mdl(self):
        simple_activity_log = []
        for _ in range(100):
            simple_activity_log.append(['A', 'B'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg = PatternDfg.create_from_event_log(log)

        pdfg = dfg.fold({Sequence.from_activity_list(['A', 'B'])})

        dfg_mdl = compute_mdl_score_dfg(dfg, dfg, verbose=False)
        pdfg_mdl = compute_mdl_score_dfg(dfg, pdfg, verbose=False)
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

        dfg_mdl = compute_mdl_score_dfg(dfg, dfg, verbose=False)
        pdfg_mdl = compute_mdl_score_dfg(dfg, pdfg, verbose=False)
        self.assertLess(pdfg_mdl, dfg_mdl)

    def test_small_perfect_choice_with_sequences_should_lead_to_best_mdl(self):
        simple_activity_log = []
        for _ in range(20):
            simple_activity_log.append(['A', 'B1', 'B2', 'D'])
        for _ in range(10):
            simple_activity_log.append(['A', 'C1', 'C2', 'D'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg = PatternDfg.create_from_event_log(log)

        dfg_with_sequences = dfg.fold({
            Sequence.from_activity_list(['B1', 'B2']),
            Sequence.from_activity_list(['C1', 'C2'])
        })

        dfg_with_choice = dfg_with_sequences.fold({
            Choice([
                Sequence.from_activity_list(['B1', 'B2']),
                Sequence.from_activity_list(['C1', 'C2'])
            ])
        })

        dfg_mdl = compute_mdl_score_dfg(dfg, dfg)
        dfg_with_sequences_mdl = compute_mdl_score_dfg(dfg, dfg_with_sequences)
        dfg_with_choice_mdl = compute_mdl_score_dfg(dfg, dfg_with_choice)
        self.assertLess(dfg_with_sequences_mdl, dfg_mdl)
        self.assertLess(dfg_with_choice_mdl, dfg_with_sequences_mdl)

if __name__ == '__main__':
    unittest.main()