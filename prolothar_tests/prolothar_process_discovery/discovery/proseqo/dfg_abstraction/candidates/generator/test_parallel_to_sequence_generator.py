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
from prolothar_process_discovery.discovery.proseqo.pattern.parallel import Parallel
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.parallel_to_sequence_generator import ParallelToSequenceGenerator

from prolothar_common.models.eventlog import EventLog

class TestParallelToSequenceGenerator(unittest.TestCase):

    def test_generate_candidates(self):
        log = EventLog.create_from_simple_activity_log([
            ['A','0','1','2','E'],
            ['A','0','1','2','E'],
            ['A','0','1','2','E'],
            ['A','0','1','2','E'],
            ['A','0','1','2','E'],
            ['A','0','2','1','E'],
        ])

        dfg = PatternDfg.create_from_event_log(log)
        dfg_with_parallel = dfg.fold({
            Parallel([
                Singleton('1'),
                Singleton('2')
            ])
        })

        sequence_1_2 = Sequence.from_activity_list(['1', '2'])
        sequence_2_1 = Sequence.from_activity_list(['2', '1'])

        found_candidates = ParallelToSequenceGenerator().generate_candidates(
                log, dfg, dfg_with_parallel)

        self.assertFalse(found_candidates is None)
        self.assertCountEqual([sequence_1_2, sequence_2_1],
                              [c.get_pattern() for c in found_candidates])

if __name__ == '__main__':
    unittest.main()