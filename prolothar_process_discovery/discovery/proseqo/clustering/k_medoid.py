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
from typing import List

from prolothar_common.models.eventlog import EventLog
from prolothar_common.clustering.k_medoid import KMedoid as KMedoidAlgorithm
from prolothar_process_discovery.discovery.proseqo.clustering.clustering_strategy import ClusteringStrategy
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.similarity_measure import SimilarityMeasure
from prolothar_process_discovery.discovery.proseqo.clustering.split.one_cluster_per_trace import OneClusterPerTrace

class KMedoid(ClusteringStrategy):
    """implements k-medoid clustering of traces based on a similarity measure"""

    def __init__(self, n_clusters: int, similarity_measure: SimilarityMeasure,
                 random_seed: int = None):
        """create and configure a new instance of KMedoid

        Args:
            n_clusters: number of clusters the log is supposed to be devided
        """
        self.n_clusters = n_clusters
        self.similarity_measure = similarity_measure
        self.__random_seed = random_seed

    def cluster(self, log: EventLog, verbose=False) -> List[EventLog]:
        clustering = KMedoidAlgorithm(
                self.similarity_measure, random_seed=self.__random_seed,
                dissimilarity_mode=False)

        if verbose:
            print('start k-medoid clustering')
        splitted_log = OneClusterPerTrace().split(log)
        self.similarity_measure.precompute(splitted_log)
        labels, _ = clustering.cluster(
                splitted_log,
                number_of_clusters=self.n_clusters)

        if verbose:
            print('k-medoid clustering completed')

        clusters = [EventLog() for _ in range(max(labels)+1)]

        for trace,label in zip(log.traces, labels):
            clusters[label].add_trace(trace)

        return clusters

    def __repr__(self) -> str:
        return 'KMedoid<%r, %r>' % (
                self.n_clusters, self.similarity_measure)
