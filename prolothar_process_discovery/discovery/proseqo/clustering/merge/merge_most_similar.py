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

import numpy as np

class MergeMostSimilar(MergeStrategy):
    def __init__(self, similarity_measure: SimilarityMeasure):
        if not isinstance(similarity_measure, SimilarityMeasure):
            raise TypeError('similarity measure is not of class SimilarityMeasure')
        self.similarity_measure = similarity_measure
        self.similarity_matrix = None

    def merge(self, clusters: List[EventLog], verbose=False):
        if self.similarity_matrix is None:
            if verbose:
                print('compute initial similarity matrix')
            self._create_similarity_matrix(clusters)
            if verbose:
                print('computed initial similarity matrix')

        most_similar_indices = np.unravel_index(self.similarity_matrix.argmax(),
                                                self.similarity_matrix.shape)
        clusters[most_similar_indices[0]].add_traces(
                clusters[most_similar_indices[1]].traces)

        del clusters[most_similar_indices[1]]

        self.similarity_matrix = np.delete(
                self.similarity_matrix, most_similar_indices[1], axis=1)
        self.similarity_matrix = np.delete(
                self.similarity_matrix, most_similar_indices[1], axis=0)

        self.similarity_measure.precompute([clusters[most_similar_indices[0]]])
        self.similarity_matrix[most_similar_indices[0], :] = [
            self.similarity_measure.compute(
                    log_i, clusters[most_similar_indices[0]]) \
                    if i != most_similar_indices[0] else float('-inf') \
                    for i,log_i in enumerate(clusters) \
        ]
        self.similarity_matrix[:, most_similar_indices[0]] = self.similarity_matrix[most_similar_indices[0], :]

    def _create_similarity_matrix(self, clusters: List[EventLog]):
        self.similarity_matrix = self.similarity_measure.compute_similarity_matrix(clusters)

        #fill diagonal with negative value such that a cluster is not merged with itself
        np.fill_diagonal(self.similarity_matrix, float('-inf'))

    def clear_cache(self):
        """deletes all cached information"""
        self.similarity_matrix = None

    def __repr__(self) -> str:
        return 'MergeMostSimilar<%r>' % self.similarity_measure
