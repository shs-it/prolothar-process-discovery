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
from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.anomalydetection.pdfg_oc3 import PatternGraphOc3

class TestPatternGraphOc3(unittest.TestCase):

    def test_plot_data_encoding_histogram(self):
        log = EventLog.create_from_simple_activity_log([
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
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

        oc3 = PatternGraphOc3(dfg_with_patterns, log,
                              devide_by_trace_length=True,
                              compute_encoded_length_isolated=True)
        oc3.plot_data_encoding_histogram()

    def test_train_by_cantellis_inequality(self):
        log = EventLog.create_from_simple_activity_log([
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
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

        oc3 = PatternGraphOc3(dfg_with_patterns, log,
                              devide_by_trace_length=True,
                              compute_encoded_length_isolated=True)
        anomaly_detector = oc3.train_by_cantellis_inequality(0.9)

        for i,trace in enumerate(log):
            self.assertEqual(i == log.get_nr_of_traces() - 1,
                             anomaly_detector.is_anomaly(trace))

if __name__ == '__main__':
    unittest.main()
