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
from prolothar_process_discovery.discovery.proseqo.pattern.inclusive_choice import InclusiveChoice
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.pattern.clustering import Clustering
from prolothar_process_discovery.discovery.proseqo.pattern.parallel import Parallel
from prolothar_process_discovery.discovery.proseqo.pattern.loop import Loop
from prolothar_process_discovery.discovery.proseqo.greedy_cover import compute_cover
from prolothar_common.models.eventlog import EventLog

class TestGreedyCover(unittest.TestCase):

    def test_compute_cover_with_sequence_patterns_only(self):
        log = EventLog.create_from_simple_activity_log([
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','7','2','6'],
            ['0','1','2','4','5','1','2','6'],
            ['0','7','8','6']
        ])

        sequence_1_2 = Sequence([Singleton('1'), Singleton('2')])

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('0', '[1,2]')
        dfg_with_patterns.add_count('[1,2]', '[4,5]')
        dfg_with_patterns.add_count('[1,2]', '6')
        dfg_with_patterns.add_count('[4,5]', '[1,2]')
        dfg_with_patterns.add_count('[4,5]', '[4,5]')
        dfg_with_patterns.add_pattern('[1,2]', sequence_1_2)
        dfg_with_patterns.add_pattern(
                '[4,5]', Sequence([Singleton('4'), Singleton('5')]))

        cover = compute_cover(log.traces, dfg_with_patterns)

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(11, # 10 mal offensichtlich, das 11. mal um von 0 nach 6 zu kommen
                usage_per_pattern[sequence_1_2.get_activity_name()])

        self.assertEqual(52, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(3, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(2, cover.move_stream.get_number_of_model_moves())
        self.assertEqual(log.count_nr_of_events(),
                         (cover.move_stream.get_number_of_synchronous_moves() +
                          cover.move_stream.get_number_of_log_moves()))

    def test_compute_cover_with_choice_pattern_only(self):
        log = EventLog.create_from_simple_activity_log([
            ['0','1','2','4'],
            ['0','1','2','4'],
            ['0','1','2','4'],
            ['0','1','3','4'],
            ['0','1','5','3','4'],
            ['0','4']
        ])

        choice_2_3 = Choice([Singleton('2'), Singleton('3')])

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('0', '1')
        dfg_with_patterns.add_count('1', '(2|3)')
        dfg_with_patterns.add_count('(2|3)', '4')
        dfg_with_patterns.add_pattern('(2|3)', choice_2_3)

        cover = compute_cover(log.traces, dfg_with_patterns)

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(6, usage_per_pattern[choice_2_3.get_activity_name()])

        self.assertEqual(3, cover.meta_stream.get_code_count(choice_2_3, '2'))
        self.assertEqual(2, cover.meta_stream.get_code_count(choice_2_3, '3'))

        self.assertEqual(22, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(1, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(2, cover.move_stream.get_number_of_model_moves())
        self.assertEqual(log.count_nr_of_events(),
                         (cover.move_stream.get_number_of_synchronous_moves() +
                          cover.move_stream.get_number_of_log_moves()))

    def test_compute_cover_with_nested_optional_pattern(self):
        log = EventLog.create_from_simple_activity_log([
            ['0','1','2','3'],
            ['0','1','2','3'],
            ['0','1','2','3'],
            ['0','1','3'],
            ['0','1','3'],
        ])

        nested_pattern = Sequence([Singleton('1'), Optional(Singleton('2')), Singleton('3')])

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('0', '[1,2?,3]')
        dfg_with_patterns.add_pattern('[1,2?,3]', nested_pattern)

        cover = compute_cover(log.traces, dfg_with_patterns)

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(5, usage_per_pattern[nested_pattern.get_activity_name()])

        self.assertEqual(18, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_model_moves())
        self.assertEqual(3, cover.meta_stream.get_code_count(
                Optional(Singleton('2')), 'present'))
        self.assertEqual(2, cover.meta_stream.get_code_count(
                Optional(Singleton('2')), 'absent'))

    def test_compute_cover_with_optional_pattern_only(self):
        log = EventLog.create_from_simple_activity_log([
            ['0','1','2','4'],
            ['0','1','2','4'],
            ['0','1','2','4'],
            ['0','1','4'],
            ['0','1','4'],
            ['0','4']
        ])

        optional_2 = Optional(Singleton('2'))

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('0', '1')
        dfg_with_patterns.add_count('1', '2?')
        dfg_with_patterns.add_count('2?', '4')
        dfg_with_patterns.add_pattern('2?', optional_2)

        cover = compute_cover(log.traces, dfg_with_patterns)

        self.assertEqual(20, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(1, cover.move_stream.get_number_of_model_moves())

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(6, usage_per_pattern[optional_2.get_activity_name()])

        self.assertEqual(3, cover.meta_stream.get_code_count(
                optional_2, 'present'))
        self.assertEqual(3, cover.meta_stream.get_code_count(
                optional_2, 'absent'))

    def test_compute_cover_with_optional_pattern_only_one_trace(self):
        log = EventLog.create_from_simple_activity_log([
            ['0','1','2','4'],
        ])

        optional_2 = Optional(Singleton('2'))

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('0', '1')
        dfg_with_patterns.add_count('1', '2?')
        dfg_with_patterns.add_count('2?', '4')
        dfg_with_patterns.add_pattern('2?', optional_2)

        cover = compute_cover(log.traces, dfg_with_patterns)

        self.assertEqual(4, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_model_moves())

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(1, usage_per_pattern[optional_2.get_activity_name()])

        self.assertEqual(1, cover.meta_stream.get_code_count(
                optional_2, 'present'))
        self.assertEqual(0, cover.meta_stream.get_code_count(
                optional_2, 'absent'))

    def test_compute_cover_with_subgraph_pattern_only(self):
        log = EventLog.create_from_simple_activity_log([
            ['0','1','2','4'],
            ['0','1','2','4'],
            ['0','1','5','2','4'],
            ['0','1','4'],
            ['0','1','4'],
            ['0','4']
        ])

        community_pdfg = PatternDfg()
        community_pdfg.add_count('1', '2')
        community = SubGraph(community_pdfg, ['1'], ['2'])

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('0', '[{1},...,{2}]')
        dfg_with_patterns.add_count('[{1},...,{2}]', '4')
        dfg_with_patterns.add_pattern('[{1},...,{2}]', community)

        cover = compute_cover(log.traces, dfg_with_patterns)

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(6, usage_per_pattern[community.get_activity_name()])

        self.assertEqual(20, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(1, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(4, cover.move_stream.get_number_of_model_moves())
        self.assertEqual(log.count_nr_of_events(),
                         (cover.move_stream.get_number_of_synchronous_moves() +
                          cover.move_stream.get_number_of_log_moves()))

    def test_compute_cover_with_nested_subgraph(self):
        log = EventLog.create_from_simple_activity_log([
            ['A','B','D','E'],
            ['A','B','D','E'],
            ['A','B','D','E'],
            ['A','C','D','E'],
            ['A','C','D','E'],
        ])
        community_pdfg = PatternDfg()
        community_pdfg.add_count('A', 'B')
        community_pdfg.add_count('A', 'C')
        community_pdfg.add_count('B', 'D')
        community_pdfg.add_count('C', 'D')
        community = SubGraph(community_pdfg, ['A'], ['D'])

        dfg_without_patterns = PatternDfg.create_from_event_log(log)
        dfg_with_patterns = dfg_without_patterns.fold([
                Sequence([community, Singleton('E')])
        ])

        cover = compute_cover(log.traces, dfg_with_patterns)
        self.assertEqual(20, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_model_moves())

    def test_compute_cover_with_clustering_pattern_only(self):
        cluster_name = '([{1},...,{2}]|[{1},...,{3}]|[{2},...,{3}])'
        log = EventLog.create_from_simple_activity_log([
            ['A', '1', '2', 'E'],
            ['A', '1', '3', 'E'],
            ['A', '2', '3', 'E'],
            ['A', '1', '3', '2', 'E'],
            ['A', '1', 'E'],
        ])

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
            log.traces[3]: 0,
            log.traces[4]: 0,
        })

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('A', cluster_name)
        dfg_with_patterns.add_count(cluster_name, 'E')
        dfg_with_patterns.add_pattern(cluster_name, cluster_pattern)

        cover = compute_cover(log.traces, dfg_with_patterns)

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(5, usage_per_pattern[cluster_pattern.get_activity_name()])

        self.assertEqual(19, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(1, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(1, cover.move_stream.get_number_of_model_moves())
        self.assertEqual(log.count_nr_of_events(),
                         (cover.move_stream.get_number_of_synchronous_moves() +
                          cover.move_stream.get_number_of_log_moves()))

    def test_cover_with_parallel_log_and_model_moves(self):
        log = EventLog.create_from_simple_activity_log([
            ['0', 'A', 'B', 'C', 'D', '1'],
            ['0', 'A', 'E', 'C', '1'],
        ])

        parallel_pattern = Parallel([Singleton('A'), Singleton('B'),
                                     Sequence.from_activity_list(['C','D'])])

        dfg = PatternDfg()
        dfg.add_count('0', '(A||B||[C,D])')
        dfg.add_count('(A||B||[C,D])', '1')
        dfg.add_pattern('(A||B||[C,D])', parallel_pattern)

        cover = compute_cover(log.traces, dfg)

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(2, usage_per_pattern[parallel_pattern.get_activity_name()])

        self.assertEqual(10, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(1, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(2, cover.move_stream.get_number_of_model_moves())
        self.assertEqual(log.count_nr_of_events(),
                         (cover.move_stream.get_number_of_synchronous_moves() +
                          cover.move_stream.get_number_of_log_moves()))

    def test_cover_with_parallel_only_sync_moves(self):
        log = EventLog.create_from_simple_activity_log([
            ['0', 'A', 'B', 'C', 'D', '1'],
            ['0', 'B', 'A', 'C', 'D', '1'],
            ['0', 'C', 'A', 'B', 'D', '1'],
        ])

        parallel_pattern = Parallel([Singleton('A'), Singleton('B'),
                                     Sequence.from_activity_list(['C','D'])])

        dfg = PatternDfg()
        dfg.add_count('0', '(A||B||[C,D])')
        dfg.add_count('(A||B||[C,D])', '1')
        dfg.add_pattern('(A||B||[C,D])', parallel_pattern)

        cover = compute_cover(log.traces, dfg)

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(3, usage_per_pattern[parallel_pattern.get_activity_name()])

        self.assertEqual(18, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_model_moves())
        self.assertEqual(log.count_nr_of_events(),
                         (cover.move_stream.get_number_of_synchronous_moves() +
                          cover.move_stream.get_number_of_log_moves()))

    def test_cover_with_loop(self):
        log = EventLog.create_from_simple_activity_log([
            ['A', 'B', 'B', 'C'],
            ['A', 'B', 'C'],
            ['A', 'B', 'B', 'B', 'C'],
            ['A', 'C'],
            ['A', 'B', 'D', 'B', 'C'],
        ])

        loop = Loop(Singleton('B'))

        dfg = PatternDfg()
        dfg.add_count('A', 'B+')
        dfg.add_count('B+', 'C')
        dfg.add_pattern('B+', loop)

        cover = compute_cover(log.traces, dfg)

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(5, usage_per_pattern[loop.get_activity_name()])

        self.assertEqual(18, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(1, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(1, cover.move_stream.get_number_of_model_moves())
        self.assertEqual(log.count_nr_of_events(),
                         (cover.move_stream.get_number_of_synchronous_moves() +
                          cover.move_stream.get_number_of_log_moves()))

        self.assertEqual(3, cover.meta_stream.get_code_count(
                loop, 'repeat0'))
        self.assertEqual(1, cover.meta_stream.get_code_count(
                loop, 'repeat1'))
        self.assertEqual(0, cover.meta_stream.get_code_count(
                loop, 'repeat2'))
        self.assertEqual(2, cover.meta_stream.get_code_count(
                loop, 'end0'))
        self.assertEqual(2, cover.meta_stream.get_code_count(
                loop, 'end1'))
        self.assertEqual(1, cover.meta_stream.get_code_count(
                loop, 'end2'))
        self.assertEqual(0, cover.meta_stream.get_code_count(
                loop, 'end3'))

    def test_cover_with_inclusive_choice(self):
        log = EventLog.create_from_simple_activity_log([
            ['0', 'A', 'B', 'C', 'D', '1'],
            ['0', 'A', 'C', 'B', '1'],
            ['0', 'A', 'C', 'D', 'A', '1'],
        ])

        choice = InclusiveChoice([Singleton('A'),
                                  Singleton('B'),
                                  Singleton('C'),
                                  Singleton('D')])

        dfg = PatternDfg()
        dfg.add_count('0', '(A,B,C,D)')
        dfg.add_count('(A,B,C,D)', '1')
        dfg.add_pattern('(A,B,C,D)', choice)

        cover = compute_cover(log.traces, dfg)

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(3, usage_per_pattern[choice.get_activity_name()])

        self.assertEqual(16, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(1, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_model_moves())
        self.assertEqual(log.count_nr_of_events(),
                         (cover.move_stream.get_number_of_synchronous_moves() +
                          cover.move_stream.get_number_of_log_moves()))

        self.assertEqual(3, cover.meta_stream.get_code_count(
                choice, 'A'))
        self.assertEqual(2, cover.meta_stream.get_code_count(
                choice, 'B'))
        self.assertEqual(3, cover.meta_stream.get_code_count(
                choice, 'C'))
        self.assertEqual(2, cover.meta_stream.get_code_count(
                choice, 'D'))

    def test_cover_with_noisy_sequence(self):
        log = EventLog.create_from_simple_activity_log([
            ['0','1','2','3'],
            ['0','4','1','4','5','2','3']
        ])

        sequence_1_2 = Sequence([Singleton('1'), Singleton('2')],
                                special_noise_set={'4'})

        dfg_with_patterns = PatternDfg.create_from_event_log(log)
        dfg_with_patterns = dfg_with_patterns.fold([sequence_1_2])

        cover = compute_cover(log.traces, dfg_with_patterns)

        usage_per_pattern = cover.pattern_stream.get_usage_per_pattern()
        self.assertEqual(2, usage_per_pattern[sequence_1_2.get_activity_name()])

        self.assertEqual(10, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(1, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_model_moves())
        self.assertEqual(log.count_nr_of_events(),
                         (cover.move_stream.get_number_of_synchronous_moves() +
                          cover.move_stream.get_number_of_log_moves()))

    def test_cover_with_storing_patterns(self):
        log = EventLog.create_from_simple_activity_log([
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','7','2','6'],
            ['0','1','2','4','5','1','2','6'],
            ['0','7','8','6']
        ])

        sequence_1_2 = Sequence([Singleton('1'), Singleton('2')])

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('0', '[1,2]')
        dfg_with_patterns.add_count('[1,2]', '[4,5]')
        dfg_with_patterns.add_count('[1,2]', '6')
        dfg_with_patterns.add_count('[4,5]', '[1,2]')
        dfg_with_patterns.add_count('[4,5]', '[4,5]')
        dfg_with_patterns.add_pattern('[1,2]', sequence_1_2)
        dfg_with_patterns.add_pattern(
                '[4,5]', Sequence([Singleton('4'), Singleton('5')]))

        cover = compute_cover(log.traces, dfg_with_patterns)
        try:
            cover.pattern_stream.get_sequence_of_added_patterns()
            self.fail('should lead to a ValueError')
        except ValueError:
            pass

        cover = compute_cover(log.traces, dfg_with_patterns,
                              store_patterns_in_pattern_stream=True)

        self.assertEqual(
            ('[0, [1,2], [4,5], [4,5], [1,2], 6, '
             '0, [1,2], [4,5], [4,5], [1,2], 6, '
             '0, [1,2], [4,5], [4,5], [4,5], [1,2], 6, '
             '0, [1,2], [4,5], [4,5], [1,2], 7, 6, '
             '0, [1,2], [4,5], [1,2], 6, '
             '0, 7, 8, [1,2], 6]'),
            str(cover.pattern_stream.get_sequence_of_added_patterns()))

    def test_compressing_start_activity_should_not_increase_log_moves(self):
        simple_activity_log = []
        for _ in range(50):
            simple_activity_log.append(['START', 'HWOE', 'HWOZ', 'WLVG'])
            simple_activity_log.append(['START', 'BRWA', 'STOE', 'STOZ', 'WLVG'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg = PatternDfg.create_from_event_log(log)

        folded_dfg = dfg.fold([
            Sequence([
                Singleton('START'),
                Choice([
                    Sequence.from_activity_list(['BRWA', 'STOE', 'STOZ']),
                    Sequence.from_activity_list(['HWOE', 'HWOZ']),
                ])
            ])
        ])

        cover_dfg = compute_cover(log.traces, dfg)
        cover_folded_dfg = compute_cover(log.traces, folded_dfg)

        self.assertDictEqual(
                cover_dfg.move_stream.count_move_codes(),
                cover_folded_dfg.move_stream.count_move_codes())

    def test_model_move_skip_patterns(self):
        log = EventLog.create_from_simple_activity_log([
                ['A','1','2','3','4','Z'],
        ])
        pattern_dfg = PatternDfg.create_from_event_log(log).fold([
                Sequence.from_activity_list(['1', '2']),
                Sequence.from_activity_list(['3', '4']),
        ])
        log = EventLog.create_from_simple_activity_log([
                ['A','Z'],
        ])

        cover = compute_cover(log.traces, pattern_dfg)
        self.assertEqual(2, cover.move_stream.get_number_of_synchronous_moves())
        self.assertEqual(0, cover.move_stream.get_number_of_log_moves())
        self.assertEqual(4, cover.move_stream.get_number_of_model_moves())
        self.assertEqual(log.count_nr_of_events(),
                         (cover.move_stream.get_number_of_synchronous_moves() +
                          cover.move_stream.get_number_of_log_moves()))

if __name__ == '__main__':
    unittest.main()
