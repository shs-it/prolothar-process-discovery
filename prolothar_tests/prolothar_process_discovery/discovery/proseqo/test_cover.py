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
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.greedy_cover import compute_cover
from prolothar_common.models.eventlog import EventLog

class TestGreedyCover(unittest.TestCase):

    def test_get_pattern_dfg_with_restored_counts(self):
        simple_activity_log = []
        for _ in range(20):
            simple_activity_log.append(['0','1','2','4','5','4','5','1','2','6'])
            simple_activity_log.append(['0','1','2','4','5','4','5','4','5','1','2','6'])
            simple_activity_log.append(['0','1','2','4','5','1','2','6'])
            simple_activity_log.append(['0','7','8','6'])
        simple_activity_log.append(['0','7','8','2','6'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg_without_patterns = PatternDfg.create_from_event_log(log)
        cover = compute_cover(log.traces, dfg_without_patterns,
                              store_patterns_in_pattern_stream=True)
        dfg = cover.get_pattern_dfg_with_restored_counts()
        self.assertEqual(dfg_without_patterns, dfg)

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

        cover = compute_cover(log.traces, dfg_with_patterns,
                              store_patterns_in_pattern_stream=True)
        dfg = cover.get_pattern_dfg_with_restored_counts()
        expected_dfg = dfg_with_patterns.copy()
        expected_dfg.edges[('0','[7,8]')].count = 21
        expected_dfg.edges[('0','[1,2]')].count = 60
        expected_dfg.edges[('[1,2]','[4,5]')].count = 60
        expected_dfg.edges[('[1,2]','6')].count = 60
        expected_dfg.edges[('[4,5]','[1,2]')].count = 60
        expected_dfg.edges[('[4,5]','[4,5]')].count = 60
        expected_dfg.edges[('[7,8]','6')].count = 21

        self.assertEqual(expected_dfg, dfg)

    def test_get_pattern_dfg_with_restored_counts_optional(self):
        simple_activity_log = []
        for _ in range(20):
            simple_activity_log.append(['0','1','2'])
            simple_activity_log.append(['0','2'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)

        dfg_without_patterns = PatternDfg.create_from_event_log(log)
        cover = compute_cover(log.traces, dfg_without_patterns,
                              store_patterns_in_pattern_stream=True)
        dfg = cover.get_pattern_dfg_with_restored_counts()
        self.assertEqual(dfg_without_patterns, dfg)

        dfg_with_patterns = PatternDfg()
        dfg_with_patterns.add_count('0', '1?')
        dfg_with_patterns.add_count('1?', '2')
        dfg_with_patterns.add_pattern('1?', Optional(Singleton('1')))

        cover = compute_cover(log.traces, dfg_with_patterns,
                              store_patterns_in_pattern_stream=True)
        dfg = cover.get_pattern_dfg_with_restored_counts()
        expected_dfg = dfg_with_patterns.copy()
        expected_dfg.edges[('0','1?')].count = 40
        expected_dfg.edges[('1?','2')].count = 40
        self.assertEqual(expected_dfg, dfg)

if __name__ == '__main__':
    unittest.main()