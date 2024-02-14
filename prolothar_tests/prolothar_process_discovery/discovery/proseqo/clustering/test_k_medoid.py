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
from prolothar_process_discovery.discovery.proseqo.clustering.k_medoid import KMedoid
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.activity_set_similarity import ActivitySetSimilarity
from prolothar_common.models.eventlog import EventLog
import pandas as pd
from prolothar_common.collections import set_similarity

class TestKMedoid(unittest.TestCase):

    def test_cluster(self):
        csv_log = pd.read_csv(
                'prolothar_tests/resources/logs/example_log_for_clustering.csv',
                delimiter=',')

        log = EventLog.create_from_pandas_df(
                csv_log, 'TraceId', 'Activity',
                event_attribute_columns=['Duration'],
                trace_attribute_columns=['DayInWeek'])

        clusters = KMedoid(3, ActivitySetSimilarity(
                set_similarity.jaccard_index), random_seed=42).cluster(log)
        self.assertEqual(3, len(clusters))
        self.assertIsInstance(clusters[0], EventLog)

if __name__ == '__main__':
    unittest.main()
