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
from prolothar_process_discovery.discovery.proseqo.greedy_cover import compute_cover
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score
from prolothar_process_discovery.discovery.proseqo.mdl_score import estimate_mdl_score
from prolothar_common.models.eventlog import EventLog

from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.candidate_generator_builder import CandidateGeneratorBuilder


class TestMdlEstimation(unittest.TestCase):

    def test_estimate_mdl_on_simple_log_and_dfg(self):
        simple_activity_log = []
        for _ in range(200):
            simple_activity_log.append(['0','1','2','4','5','4','5','1','2','6'])
            simple_activity_log.append(['0','1','2','4','5','4','5','4','5','1','2','6'])
            simple_activity_log.append(['0','1','2','4','5','1','2','6'])
            simple_activity_log.append(['0','7','8','6'])
        for _ in range(1):
            simple_activity_log.append(['0','7','8','2','6'])
        log = EventLog.create_from_simple_activity_log(
                simple_activity_log)

        dfg = PatternDfg.create_from_event_log(log)
        cover_on_dfg = compute_cover(log.traces, dfg)
        original_mdl = compute_mdl_score(log, dfg)

        candidate_generator = CandidateGeneratorBuilder()\
            .with_edge_removals()\
            .with_node_removals()\
            .with_sequences()\
            .with_loops()\
            .build()

        for candidate in candidate_generator.generate_candidates(log, dfg, dfg):
            candidate_dfg = dfg.copy()
            candidate.apply_on_dfg(candidate_dfg)
            true_mdl = compute_mdl_score(log, candidate_dfg)
            estimated_mdl = estimate_mdl_score(
                    dfg, cover_on_dfg, candidate, log, dfg)
            if str(candidate).startswith("remove edge"):
                self.assertLess(estimated_mdl - 6, true_mdl)
            if true_mdl < original_mdl and str(candidate) != 'remove node: 0':
                print(candidate)
                self.assertLess(estimated_mdl, original_mdl)

    # def test_estimate_mdl_on_simple_log_and_pattern_dfg(self):
    #     simple_activity_log = []
    #     for _ in range(200):
    #         simple_activity_log.append(['0','1','2','4','5','4','5','1','2','6'])
    #         simple_activity_log.append(['0','1','2','4','5','4','5','4','5','1','2','6'])
    #         simple_activity_log.append(['0','1','2','4','5','1','2','6'])
    #         simple_activity_log.append(['0','7','8','6'])
    #     for _ in range(1):
    #         simple_activity_log.append(['0','7','8','2','6'])
    #     log = EventLog.create_from_simple_activity_log(
    #             simple_activity_log)

    #     dfg = PatternDfg.create_from_event_log(log)
    #     pattern_dfg = dfg.fold([Sequence.from_activity_list(['1', '2'])])
    #     initial_cover = compute_cover(log.traces, pattern_dfg)
    #     original_mdl = compute_mdl_score(log, pattern_dfg, verbose=True)
    #     print(original_mdl)

    #     candidate_generator = CandidateGeneratorBuilder()\
    #         .with_edge_removals()\
    #         .with_node_removals()\
    #         .with_sequences()\
    #         .with_loops()\
    #         .with_sequences()\
    #         .build()

    #     for candidate in candidate_generator.generate_candidates(log, dfg, pattern_dfg):
    #         candidate_dfg = dfg.copy()
    #         candidate.apply_on_dfg(candidate_dfg)
    #         true_mdl = compute_mdl_score(log, candidate_dfg)
    #         estimated_mdl = estimate_mdl_score(
    #                 pattern_dfg, initial_cover, candidate, log, dfg)
    #         if str(candidate).startswith("remove edge"):
    #             self.assertLess(estimated_mdl - 6, true_mdl)
    #         else:
    #             print('===============')
    #             print(candidate)
    #             print('------')
    #             compute_mdl_score(log, candidate_dfg, verbose=True)
    #             print(true_mdl)
    #             print('------')
    #             estimate_mdl_score(
    #                     pattern_dfg, initial_cover, candidate, log, dfg,
    #                     verbose=True)
    #             print(estimated_mdl)
    #         if true_mdl < original_mdl and str(candidate) != 'remove node: 0':
    #             self.assertLess(estimated_mdl, original_mdl)

if __name__ == '__main__':
    unittest.main()
