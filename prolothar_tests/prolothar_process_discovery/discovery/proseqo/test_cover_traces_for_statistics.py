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
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton

from prolothar_process_discovery.discovery.proseqo.cover_traces_for_statistics import count_moves

import pandas as pd

class TestCoverTracesForStatistics(unittest.TestCase):

    def test_count_moves_with_sequence_patterns_only(self):
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

        move_df = count_moves(log.traces, dfg_with_patterns)
        self.assertTrue(move_df is not None)

        expected_df = pd.DataFrame(data=[
            [['0','1','2','4','5','4','5','1','2','6'], 10, 10, 0, 0],
            [['0','1','2','4','5','4','5','1','2','6'], 10, 10, 0, 0],
            [['0','1','2','4','5','4','5','4','5','1','2','6'], 12, 12, 0, 0],
            [['0','1','2','4','5','4','5','1','7','2','6'], 11, 10, 1, 0],
            [['0','1','2','4','5','1','2','6'], 8, 8, 0, 0],
            [['0','7','8','6'], 6, 2, 2, 2]
        ], columns=['Trace', '# Moves', '# Sync Moves', '# Log Moves',
                    '# Model Moves'])

        if not expected_df.equals(move_df):
            pd.set_option('display.max_columns', 30)
            print('expected:')
            print(expected_df)
            print('actual:')
            print(move_df)
            self.fail('dataframes differ. see console output')

if __name__ == '__main__':
    unittest.main()