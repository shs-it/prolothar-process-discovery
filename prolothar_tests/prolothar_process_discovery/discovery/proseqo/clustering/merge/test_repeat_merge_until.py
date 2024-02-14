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
from prolothar_process_discovery.discovery.proseqo.clustering.merge.merge_most_similar import MergeMostSimilar
from prolothar_process_discovery.discovery.proseqo.clustering.merge.repeat_merge_while import RepeatMergeWhile
from prolothar_process_discovery.discovery.proseqo.clustering.merge.condition.merge_condition import MergeCondition
from prolothar_process_discovery.discovery.proseqo.clustering.merge.condition.number_of_clusters_greater_than import NumberOfClustersGreaterThan
from prolothar_process_discovery.discovery.proseqo.clustering.merge.condition.mdl_score_decreases import MdlScoreDecreases
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.activity_set_similarity import ActivitySetSimilarity
from prolothar_process_discovery.discovery.proseqo.clustering.split.one_cluster_per_trace import OneClusterPerTrace
from prolothar_common.models.eventlog import EventLog
import pandas as pd

from prolothar_common.collections.set_similarity import jaccard_index

class TestRepeatMergeUntil(unittest.TestCase):

    def setUp(self):
        csv_log = pd.read_csv(
                'prolothar_tests/resources/logs/example_log_for_clustering.csv',
                delimiter=',')

        log = EventLog.create_from_pandas_df(
                csv_log, 'TraceId', 'Activity',
                event_attribute_columns=['Duration'],
                trace_attribute_columns=['DayInWeek'])

        self.clusters = OneClusterPerTrace().split(log)

    def test_merge_while_score_increases(self):
        self._test_condition(MdlScoreDecreases(),
                         [[1, 2, 4, 3, 5]])

    def test_merge_while_number_of_clusters_greater_than(self):
        self._test_condition(NumberOfClustersGreaterThan(3),
                         [[1, 2, 4], [3], [5]])

    def _test_condition(self, merge_condition: MergeCondition, expected_clustering):
        RepeatMergeWhile(MergeMostSimilar(ActivitySetSimilarity(jaccard_index)),
                         merge_condition).merge(self.clusters)

        trace_ids_per_cluster = [[t.attributes['TraceId'] for t in c.traces]
                                 for c in self.clusters]
        self.assertCountEqual(expected_clustering, trace_ids_per_cluster)

if __name__ == '__main__':
    unittest.main()