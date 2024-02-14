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
from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.clustering.merge.condition.merge_condition import MergeCondition

from typing import List

class NumberOfClustersGreaterThan(MergeCondition):

    def __init__(self, min_number_of_clusters: int):
        self.min_number_of_clusters = min_number_of_clusters

    def should_merge(self, clusters: List[EventLog]) -> bool:
        return self.min_number_of_clusters < len(clusters)

    def reset(self):
        pass

    def __repr__(self) -> str:
        return 'NumberOfClustersGreaterThan<%r>' % self.min_number_of_clusters

