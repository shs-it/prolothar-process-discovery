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

import itertools

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.prune_with_mdl import PruneWithMdl
from prolothar_process_discovery.discovery.proseqo.edge_removal.termination_criterion import MaxAverageDegree
from prolothar_common.models.eventlog import EventLog
import pandas as pd

from prolothar_process_discovery.data.synthetic_baking import baking

class TestPruneWithMdlFast(unittest.TestCase):

    def test_mine_dfg_simple_example(self):
        print('test_mine_dfg_simple_example started')
        csv_log = pd.read_csv(
                'prolothar_tests/resources/logs/example_log_for_abstraction.csv',
                delimiter=',')

        log = EventLog.create_from_pandas_df(
                csv_log, 'TraceId', 'Activity',
                event_attribute_columns=['Duration'])
        dfg = PatternDfg.create_from_event_log(log)
        abstracted_dfg = PruneWithMdl(
            MaxAverageDegree(1.5), evaluation_limit='nodes',
            recompute_gain_in_every_iteration=False).mine_dfg(
                    log, dfg, verbose=True)
        self.assertEqual(1, abstracted_dfg.get_nr_of_nodes())
        self.assertIn(list(abstracted_dfg.get_nodes())[0].activity,
                      ['[StandUp,Breakfast,Bathroom,Work?,Dinner,Sleeping]',
                       '[StandUp,Breakfast?,Bathroom,Work?,Dinner,Sleeping]',
                       '[StandUp,Breakfast,Bathroom,Work,Dinner,Sleeping]'])

    def test_mine_dfg_synthetic_baking_dataset(self):
        print('test_mine_dfg_synthetic_baking_dataset started')
        log = baking.generate_log(100, use_clustering_model=True,
                                  random_seed=42)
        dfg = PatternDfg.create_from_event_log(log)
        folded_dfg = PruneWithMdl(
            MaxAverageDegree(1.5), evaluation_limit='nodes',
            recompute_gain_in_every_iteration=False).mine_dfg(
                    log, dfg, verbose=True)
        self.assertEqual(11, folded_dfg.get_nr_of_nodes())
        self.assertEqual(16, folded_dfg.get_nr_of_edges())

    def test_should_be_able_to_find_perfect_pattern_representation_1(self):
        print('test_should_be_able_to_find_perfect_pattern_representation_1 started')
        log = []
        for i in range(50):
            log.append(['START', 'a', 'f', 'g', 'END'])
            log.append(['START', 'a', 'c', 'e', 'd', 'i', 'h', 'END'])
            log.append(['START', 'a', 'b', 'END'])
        log = EventLog.create_from_simple_activity_log(log)

        dfg = PatternDfg.create_from_event_log(log)
        pattern_dfg = PruneWithMdl(
            MaxAverageDegree(1.5), evaluation_limit='nodes',
            recompute_gain_in_every_iteration=False).mine_dfg(
                    log, dfg, verbose=True)
        self.assertEqual(1, pattern_dfg.get_nr_of_nodes())
        self.assertEqual(0, pattern_dfg.get_nr_of_edges())
        self.assertEqual(
                '[START,a,([c,e,d,i,h]|[f,g]|b),END]',
                list(pattern_dfg.get_nodes())[0].activity)

    def test_should_be_able_to_find_perfect_pattern_representation_2(self):
        print('test_should_be_able_to_find_perfect_pattern_representation_2 started')
        log = []
        for i in range(10):
            log.append(['START', 'a', 'c', 'h', 'b', 'e', 'd', 'j', 'END'])
            log.append(['START', 'f', 'c', 'h', 'b', 'e', 'd', 'j', 'END'])
            log.append(['START', 'f', 'c', 'h', 'b', 'e', 'g', 'i', 'END'])
        log = EventLog.create_from_simple_activity_log(log)

        dfg = PatternDfg.create_from_event_log(log)
        pattern_dfg = PruneWithMdl(
            MaxAverageDegree(1.5), evaluation_limit='nodes',
            recompute_gain_in_every_iteration=False).mine_dfg(
                    log, dfg, verbose=False)

        self.assertEqual(1, pattern_dfg.get_nr_of_nodes())
        self.assertEqual(0, pattern_dfg.get_nr_of_edges())
        self.assertEqual(
                '[START,(a|f),c,h,b,e,([d,j]|[g,i]),END]',
                list(pattern_dfg.get_nodes())[0].activity)

    def test_prune_very_dense_graph(self):
        log = []
        for i in range(10):
            for p in itertools.permutations(['a', 'b', 'c', 'd', 'e', 'f']):
                log.append(['START'] + list(p) + ['END'])
        log = EventLog.create_from_simple_activity_log(log)

        dfg = PatternDfg.create_from_event_log(log)
        pattern_dfg = PruneWithMdl(
            MaxAverageDegree(1.5), evaluation_limit='nodes',
            recompute_gain_in_every_iteration=False).mine_dfg(
                    log, dfg, verbose=False)

        source_activities = pattern_dfg.get_source_activities()
        self.assertEqual(1, len(source_activities))

        sink_activities = pattern_dfg.get_sink_activities()
        self.assertEqual(1, len(sink_activities))

        self.assertTrue(['START'], source_activities[0])
        self.assertTrue(['END'], sink_activities[0])

if __name__ == '__main__':
    unittest.main()
