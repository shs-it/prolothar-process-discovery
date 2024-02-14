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
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.similarity_measure import SimilarityMeasure
from prolothar_process_discovery.discovery.proseqo.clustering.split.one_cluster_per_trace import OneClusterPerTrace

from typing import List

from sklearn.cluster import SpectralClustering as SklearnSpectralClustering

class SpectralClustering(ClusteringStrategy):
    """implements spectral clustering of traces based on a similarity measure"""

    def __init__(self, n_clusters: int, similarity_measure: SimilarityMeasure):
        """create and configure a new instance of SpectralClustering

        Args:
            n_clusters: number of clusters the log is supposed to be devided
        """
        self.n_clusters = n_clusters
        self.similarity_measure = similarity_measure

    def cluster(self, log: EventLog, verbose=False) -> List[EventLog]:
        clustering = SklearnSpectralClustering(
                affinity='precomputed', n_clusters=self.n_clusters)

        if verbose:
            print('start spectral clustering')
        labels = clustering.fit_predict(
                self.similarity_measure.compute_similarity_matrix(
                        OneClusterPerTrace().split(log)))
        if verbose:
            print('spectral clustering completed')

        clusters = [EventLog() for _ in range(max(labels)+1)]

        for trace,label in zip(log.traces, labels):
            clusters[label].add_trace(trace)

        return clusters

    def __repr__(self) -> str:
        return 'SpectralClustering<%r, %r>' % (
                self.n_clusters, self.similarity_measure)
