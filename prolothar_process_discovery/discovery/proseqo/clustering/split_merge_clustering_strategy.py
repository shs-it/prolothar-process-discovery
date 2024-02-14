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
from prolothar_process_discovery.discovery.proseqo.clustering.clustering_strategy import ClusteringStrategy
from prolothar_process_discovery.discovery.proseqo.clustering.split.split_strategy import SplitStrategy
from prolothar_process_discovery.discovery.proseqo.clustering.merge.merge_strategy import MergeStrategy

from typing import List

class SplitMergeClusteringStrategy(ClusteringStrategy):
    def __init__(self, split_strategy: SplitStrategy, merge_strategy: MergeStrategy):
        self.split_strategy = split_strategy
        self.merge_strategy = merge_strategy

    def cluster(self, log: EventLog, verbose=False) -> List[EventLog]:
        clusters = self.split_strategy.split(log, verbose=verbose)
        if verbose:
            print('%r splitted log into %d clusters. start merging' % (
                    self.split_strategy, len(clusters)))
        self.merge_strategy.merge(clusters, verbose=verbose)
        print('%r merged clusters into %d clusters' % (
                self.merge_strategy, len(clusters)))
        return clusters

    def __repr__(self) -> str:
        return 'SplitMergeClusteringStrategy<%r, %r>' % (
                self.split_strategy, self.merge_strategy)