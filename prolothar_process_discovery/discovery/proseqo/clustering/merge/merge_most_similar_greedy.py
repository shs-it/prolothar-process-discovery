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
from prolothar_process_discovery.discovery.proseqo.clustering.merge.merge_strategy import MergeStrategy
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.similarity_measure import SimilarityMeasure
from prolothar_common.models.eventlog import EventLog

from typing import List

class MergeMostSimilarGreedy(MergeStrategy):
    """
    greedily merges the most similar logs in the cluster. for the first log
    the similarity to all other logs is computed. Then the logs are sorted
    in descending order based on their similarity to the first log. For each
    log in this list we only compute the similarity to the first right neighbor.
    """
    def __init__(self, similarity_measure: SimilarityMeasure):
        if not isinstance(similarity_measure, SimilarityMeasure):
            raise TypeError('similarity measure is not of class SimilarityMeasure')
        if not similarity_measure.is_symmetric():
            raise ValueError('similraity measure must be symmetric')
        self.similarity_measure = similarity_measure
        self.similarity_list = None

    def merge(self, clusters: List[EventLog], verbose=False):
        if self.similarity_list is None:
            self._createSimilarityList(clusters)

        most_similar_indices = self._find_most_similar_indices()

        clusters[most_similar_indices[0]].add_traces(
                clusters[most_similar_indices[1]].traces)

        del clusters[most_similar_indices[1]]

        #TODO: replace this with an update of the similarity list
        self.similarity_list = None

    def _createSimilarityList(self, clusters: List[EventLog]):
        self.similarity_measure.precompute(clusters)
        self.similarity_list = [_ListElement(
                i+1, self.similarity_measure.compute(clusters[0], cluster),
                float('-inf')) for i,cluster in enumerate(clusters[1:])]
        self.similarity_list.sort(key=lambda e: e.similarity_to_first_cluster,
                                  reverse=True)
        for element,neighbor in zip(self.similarity_list, self.similarity_list[1:]):
            element.similarity_to_neighbor = self.similarity_measure.compute(
                    clusters[element.cluster_index],
                    clusters[neighbor.cluster_index])

    def _find_most_similar_indices(self):
        most_similar_indices = None
        max_similarity = float('-inf')
        for i,element in enumerate(self.similarity_list):
            if element.similarity_to_first_cluster > max_similarity:
                max_similarity = element.similarity_to_first_cluster
                most_similar_indices = (0,element.cluster_index)
            if element.similarity_to_neighbor > max_similarity:
                max_similarity = element.similarity_to_neighbor
                most_similar_indices = (element.cluster_index,
                                        self.similarity_list[i+1].cluster_index)
            #performance speed-up: similarity can be 1 at the maximum
            if max_similarity >= 1:
                return most_similar_indices
        return most_similar_indices

    def clear_cache(self):
        """deletes all cached information"""
        self.similarity_list = None

    def __repr__(self) -> str:
        return 'MergeMostSimilarGreedy<%r>' % self.similarity_measure

class _ListElement():
    def __init__(self, cluster_index: int, similarity_to_first_cluster: float,
                 similarity_to_neighbor: float):
        self.cluster_index = cluster_index
        self.similarity_to_first_cluster = similarity_to_first_cluster
        self.similarity_to_neighbor = similarity_to_neighbor