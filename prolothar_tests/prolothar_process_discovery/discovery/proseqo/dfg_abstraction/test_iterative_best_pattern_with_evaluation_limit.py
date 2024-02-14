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
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.iterative_best_pattern import IterativeBestPattern
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.candidate_generator_builder import CandidateGeneratorBuilder

from prolothar_common.models.eventlog import EventLog
import pandas as pd

from prolothar_process_discovery.data.synthetic_baking import baking
from datetime import timedelta, datetime

class TestIterativeBestPatternWithEvaluationLimit(unittest.TestCase):

    def test_mine_dfg_simple_example(self):
        print('test_mine_dfg_simple_example started')
        csv_log = pd.read_csv(
                'prolothar_tests/resources/logs/example_log_for_abstraction.csv',
                delimiter=',')

        log = EventLog.create_from_pandas_df(
                csv_log, 'TraceId', 'Activity',
                event_attribute_columns=['Duration'])
        abstracted_dfg = IterativeBestPattern(
                CandidateGeneratorBuilder()\
                    .with_choices().with_edge_removals().with_optionals()\
                    .with_sequences().with_loops().build(),
                max_nr_of_workers=1, candidate_pruning=True,
                evaluation_limit='nodes').mine_dfg(
                    log, PatternDfg.create_from_event_log(log), verbose=True)

        self.assertEqual(1, abstracted_dfg.get_nr_of_nodes())
        self.assertEqual('[StandUp,Breakfast,Bathroom,Work,Dinner,Sleeping]',
                         list(abstracted_dfg.get_nodes())[0].activity)

    def test_mine_dfg_synthetic_baking_dataset(self):
        print('test_mine_dfg_synthetic_baking_dataset started')
        log = baking.generate_log(100, use_clustering_model=True)

        folded_dfg = IterativeBestPattern(
                CandidateGeneratorBuilder()\
                    .with_choices().with_edge_removals().with_optionals()\
                    .with_sequences().with_loops().with_node_removals()\
                    .with_parallels()\
                    .build(), candidate_pruning=True,
                    evaluation_limit='nodes'
                ).mine_dfg(
                    log, PatternDfg.create_from_event_log(log), verbose=True)

        self.assertIn(folded_dfg.get_nr_of_nodes(), [12, 14,16])
        self.assertIn(folded_dfg.get_nr_of_edges(), [21, 22, 24,28])

    def test_should_be_able_to_find_perfect_pattern_representation_1(self):
        print('test_should_be_able_to_find_perfect_pattern_representation_1 started')
        log = []
        for i in range(50):
            log.append(['START', 'a', 'f', 'g', 'END'])
            log.append(['START', 'a', 'c', 'e', 'd', 'i', 'h', 'END'])
            log.append(['START', 'a', 'b', 'END'])
        log = EventLog.create_from_simple_activity_log(log)

        pattern_dfg = IterativeBestPattern(
                CandidateGeneratorBuilder()\
                    .with_choices().with_edge_removals().with_optionals()\
                    .with_sequences().with_loops().with_node_removals()\
                    .with_parallels().build(),
                timebudget=timedelta(seconds=30),
                candidate_pruning=True, evaluation_limit='nodes').mine_dfg(
                    log, PatternDfg.create_from_event_log(log), verbose=True)
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

        pattern_dfg = IterativeBestPattern(
                CandidateGeneratorBuilder()\
                    .with_choices().with_edge_removals().with_optionals()\
                    .with_sequences().with_loops().with_node_removals()\
                    .with_parallels().build(),
                timebudget=timedelta(seconds=30),
                max_nr_of_workers=1, candidate_pruning=True,
                evaluation_limit='nodes').mine_dfg(
                    log, PatternDfg.create_from_event_log(log), verbose=True)
        self.assertEqual(1, pattern_dfg.get_nr_of_nodes())
        self.assertEqual(0, pattern_dfg.get_nr_of_edges())
        self.assertEqual(
                '[START,(a|f),c,h,b,e,([d,j]|[g,i]),END]',
                list(pattern_dfg.get_nodes())[0].activity)

    def test_should_be_able_to_find_blob(self):
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

        pattern_dfg = IterativeBestPattern(
                CandidateGeneratorBuilder()\
                    .with_choices().with_edge_removals().with_optionals()\
                    .with_sequences().with_loops().with_node_removals()\
                    .with_parallels().with_blobs().build(),
                timebudget=timedelta(seconds=30),
                max_nr_of_workers=1, candidate_pruning=True,
                evaluation_limit='nodes').mine_dfg(
                    log, PatternDfg.create_from_event_log(log), verbose=True)

        self.assertEqual(1, pattern_dfg.get_nr_of_nodes())
        self.assertEqual(0, pattern_dfg.get_nr_of_edges())
        self.assertEqual(
                '[a,b,c,(d|{g,h,k,l}),e,f]',
                list(pattern_dfg.get_nodes())[0].activity)

if __name__ == '__main__':
    unittest.main()
