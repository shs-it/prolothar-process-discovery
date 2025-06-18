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
from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import apply_candidate
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import CandidateEdgeRemoval
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import CandidatePattern
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import infer_candidates

from prolothar_process_discovery.data.synthetic_baking import baking

class TestCandidates(unittest.TestCase):

    def test_apply_candidates(self):
        log = baking.generate_log(100, use_clustering_model=True)

        dfg = PatternDfg.create_from_event_log(log)

        selected_candidates = []

        _,selected_candidates = apply_candidate(
                dfg, selected_candidates,
                CandidateEdgeRemoval([
                        dfg.edges[('Stir', 'Add Baking Powder')]]))
        self.assertEqual(1, len(selected_candidates))

        _,selected_candidates = apply_candidate(
                dfg, selected_candidates,
                CandidateEdgeRemoval([
                        dfg.edges[('Add Baking Powder', 'Stir')]]))
        self.assertEqual(2, len(selected_candidates))

        _,selected_candidates = apply_candidate(
                dfg, selected_candidates,
                CandidatePattern(Sequence.from_activity_list([
                        'Eat', 'Smile', 'End'])))
        self.assertEqual(3, len(selected_candidates))

        _,selected_candidates = apply_candidate(
                dfg, selected_candidates,
                CandidateEdgeRemoval([
                        dfg.edges[('Take out of the Oven',
                                  'Sprinkle with Icing Sugar')]]))
        self.assertEqual(4, len(selected_candidates))

        dfg,selected_candidates = apply_candidate(
                dfg, selected_candidates,
                CandidatePattern(Sequence.from_activity_list([
                        'Take out of the Oven', 'Sprinkle with Icing Sugar',
                        'Eat', 'Smile', 'End'])))
        self.assertEqual(4, len(selected_candidates))

    def test_apply_candidates_pattern_should_keep_removing_edges_of_subpatterns(self):
        log = []
        for i in range(10):
            log.append(['START', 'a', 'c', 'h', 'b', 'e', 'd', 'j', 'END'])
            log.append(['START', 'f', 'c', 'h', 'b', 'e', 'd', 'j', 'END'])
            log.append(['START', 'f', 'c', 'h', 'b', 'e', 'g', 'i', 'END'])
        log = EventLog.create_from_simple_activity_log(log)

        original_dfg = PatternDfg.create_from_event_log(log)

        selected_candidates = [
                CandidateEdgeRemoval([original_dfg.edges[('b','e')]])
        ]

        dfg,selected_candidates = apply_candidate(
                original_dfg,
                selected_candidates,
                CandidatePattern(Sequence.from_activity_list(['h', 'b'])))

        self.assertEqual(2, len(selected_candidates))
        self.assertTrue('[h,b]' in dfg.nodes)
        self.assertTrue(('[h,b]','e') not in dfg.edges)

    def test_infer_candidates(self):
        log = []
        for i in range(10):
            log.append(['START', 'a', 'c', 'h', 'b', 'e', 'd', 'j', 'END'])
            log.append(['START', 'f', 'c', 'h', 'b', 'e', 'd', 'j', 'END'])
            log.append(['START', 'f', 'c', 'h', 'b', 'e', 'g', 'i', 'END'])
        log = EventLog.create_from_simple_activity_log(log)

        dfg = PatternDfg.create_from_event_log(log)
        self.assertEqual(0, len(infer_candidates(dfg, dfg)))

        pattern_dfg = dfg.fold({Sequence.from_activity_list(['h', 'b'])})
        self.assertEqual(1, len(infer_candidates(dfg, pattern_dfg)))

        pattern_dfg.remove_edge(('c', '[h,b]'))
        self.assertEqual(2, len(infer_candidates(dfg, pattern_dfg)))

if __name__ == '__main__':
    unittest.main()