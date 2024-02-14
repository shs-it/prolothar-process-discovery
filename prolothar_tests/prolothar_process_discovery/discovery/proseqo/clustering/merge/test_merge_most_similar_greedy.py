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
from prolothar_process_discovery.discovery.proseqo.clustering.merge.merge_most_similar_greedy import MergeMostSimilarGreedy
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.activity_set_similarity import ActivitySetSimilarity
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.dfg_edge_set_similarity import DfgEdgeSetSimilarity
from prolothar_process_discovery.discovery.proseqo.clustering.split.one_cluster_per_trace import OneClusterPerTrace
from prolothar_common.models.eventlog import EventLog
import pandas as pd

from prolothar_common.collections.set_similarity import jaccard_index

class TestMergeMostSimilar(unittest.TestCase):

    def setUp(self):
        csv_log = pd.read_csv(
                'prolothar_tests/resources/logs/example_log_for_clustering.csv',
                delimiter=',')

        log = EventLog.create_from_pandas_df(
                csv_log, 'TraceId', 'Activity',
                event_attribute_columns=['Duration'],
                trace_attribute_columns=['DayInWeek'])

        self.clusters = OneClusterPerTrace().split(log)

    def test_merge_activity_set_jaccard_index(self):
        self._test_similarity_measure(ActivitySetSimilarity(jaccard_index),
                                      [[1, 2], [4], [3], [5]])

    def test_merge_edge_set_jaccard_index(self):
        self._test_similarity_measure(DfgEdgeSetSimilarity(jaccard_index),
                                      [[1, 2], [4], [3], [5]])

    def _test_similarity_measure(self, similarity_measure, expected_clustering):
        MergeMostSimilarGreedy(similarity_measure).merge(self.clusters)
        self.assertEqual(4, len(self.clusters))

        trace_ids_per_cluster = [[t.attributes['TraceId'] for t in c.traces]
                                 for c in self.clusters]
        self.assertCountEqual(expected_clustering, trace_ids_per_cluster)

if __name__ == '__main__':
    unittest.main()