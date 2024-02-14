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
from prolothar_process_discovery.conformance.logdistance.pdfg_log_distance import PatternDfgLogdistance
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.conformance.logdistance.greedy_min_edit_distance import GreedyMinEditLogDistance

class TestPatternDfgLogDistance(unittest.TestCase):

    def test_compute(self):
        distance = PatternDfgLogdistance(GreedyMinEditLogDistance())

        simple_activity_log = []
        for _ in range(10):
            simple_activity_log.append(['0','1','2','4','5','4','5','1','2','6'])
            simple_activity_log.append(['0','1','2','4','5','4','5','4','5','1','2','6'])
            simple_activity_log.append(['0','1','2','4','5','1','2','6'])
            simple_activity_log.append(['0','7','8','6'])
        simple_activity_log.append(['0','7','8','2','6'])
        log = EventLog.create_from_simple_activity_log(simple_activity_log)
        dfg = PatternDfg.create_from_event_log(log)
        distance_of_dfg = distance.compute(dfg, log, random_seed=42)

        dfg_with_missing_edges = PatternDfg()
        dfg_with_missing_edges.add_count('0', '1')
        dfg_with_missing_edges.add_count('0', '7')
        dfg_with_missing_edges.add_count('2', '4')
        dfg_with_missing_edges.add_count('2', '6')
        dfg_with_missing_edges.add_count('5', '1')
        dfg_with_missing_edges.add_count('5', '4')
        dfg_with_missing_edges.add_count('7', '8')
        dfg_with_missing_edges.add_count('8', '6')
        distance_of_dfg_with_missing_edges = distance.compute(
                dfg_with_missing_edges, log, random_seed=42)

        dfg_with_patterns = dfg.fold([
                Sequence([Singleton('1'), Singleton('2')]),
                Sequence([Singleton('4'), Singleton('5')]),
                Sequence([Singleton('7'), Singleton('8')]),
        ])
        distance_of_dfg_with_patterns = distance.compute(
                dfg_with_patterns, log, random_seed=42)

        self.assertLess(distance_of_dfg, distance_of_dfg_with_missing_edges)
        self.assertLess(distance_of_dfg_with_patterns,
                        distance_of_dfg_with_missing_edges)

if __name__ == '__main__':
    unittest.main()
