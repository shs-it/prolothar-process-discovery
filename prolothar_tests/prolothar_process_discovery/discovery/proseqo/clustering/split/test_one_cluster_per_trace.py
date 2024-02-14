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
from prolothar_process_discovery.discovery.proseqo.clustering.split.one_cluster_per_trace import OneClusterPerTrace
from prolothar_common.models.eventlog import EventLog
import pandas as pd

class TestSplitByDiscreteTraceAttribute(unittest.TestCase):

    def test_split(self):
        csv_log = pd.read_csv(
                'prolothar_tests/resources/logs/example_log_for_clustering.csv',
                delimiter=',')

        log = EventLog.create_from_pandas_df(
                csv_log, 'TraceId', 'Activity',
                event_attribute_columns=['Duration'],
                trace_attribute_columns=['DayInWeek'])

        clusters = OneClusterPerTrace().split(log)
        self.assertEqual(5, len(clusters))

        trace_ids_per_cluster = [[t.attributes['TraceId'] for t in c.traces]
                                 for c in clusters]
        self.assertCountEqual([[1], [4], [2], [3], [5]], trace_ids_per_cluster)


if __name__ == '__main__':
    unittest.main()