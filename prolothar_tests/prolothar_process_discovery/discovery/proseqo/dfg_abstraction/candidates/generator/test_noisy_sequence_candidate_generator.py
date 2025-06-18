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
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.noisy_sequence_candidate_generator import NoisySequenceCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score

from prolothar_common.models.eventlog import EventLog

class TestNoisySequenceCandidateGenerator(unittest.TestCase):

    def test_generate_candidates(self):
        log = EventLog.create_from_simple_activity_log([
            ['A','0','1','2','C','E'],
            ['B','0','4','1','4','5','2','D'],
            ['B','0','1','4','2','D'],
            ['B','0','1','2','4','C']
        ])

        sequence_1_2 = Sequence(
                [
                        Singleton('1'),
                        Singleton('5'),
                        Singleton('2'),
                        Singleton('C')
                ], special_noise_set={'4'})

        dfg = PatternDfg.create_from_event_log(log)
        found_candidates = NoisySequenceCandidateGenerator().generate_candidates(
                log, dfg, dfg)

        self.assertFalse(found_candidates is None)
        self.assertCountEqual([sequence_1_2],
                              [c.get_pattern() for c in found_candidates])

        dfg = PatternDfg.create_from_event_log(log)
        mdl_dfg = compute_mdl_score(log, dfg)
        mdl_pattern = compute_mdl_score(log, dfg.fold({sequence_1_2}))
        self.assertLess(mdl_pattern, mdl_dfg)

    def test_generate_candidates_with_optional(self):
        log = EventLog.create_from_simple_activity_log([
            ['B','0','1','4','2','D'],
            ['B','0','1','4','2','D'],
            ['B','0','1','4','2','D'],
            ['B','0','1','4','2','D'],
            ['B','0','4','1','2','D'],
            ['B','0','4','1','2','D'],
            ['B','0','4','1','2','D'],
            ['B','0','4','1','2','D'],
            ['B','0','4','1','2','D'],
            ['B','0','4','1','2','D'],
            ['B','0','1','2','4','C'],
            ['B','0','1','2','4','C'],
            ['B','0','1','2','4','C'],
            ['B','0','1','2','4','C'],
            ['B','0','1','4','C'],
            ['B','0','1','4','C'],
            ['B','0','1','4','C'],
            ['B','0','1','4','C'],
            ['B','0','1','4','C'],
            ['B','0','1','4','C'],
            ['B','0','1','4','D'],
            ['B','0','1','4','D'],
            ['B','0','1','4','D'],
            ['B','0','1','4','D'],
            ['B','0','1','4','D']
        ])

        sequence_1_2 = Sequence([Singleton('1'),
                                 Optional(Singleton('2')),
                                 Choice([Singleton('C'), Singleton('D')])],
                                special_noise_set={'4'})

        dfg = PatternDfg.create_from_event_log(log)
        found_candidates = NoisySequenceCandidateGenerator().generate_candidates(
                log, dfg, dfg)

        self.assertFalse(found_candidates is None)
        self.assertCountEqual([sequence_1_2],
                              [c.get_pattern() for c in found_candidates])

if __name__ == '__main__':
    unittest.main()