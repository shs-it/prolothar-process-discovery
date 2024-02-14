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
from abc import ABC, abstractmethod

from prolothar_common.models.eventlog import EventLog

from typing import List

import numpy as np

class SimilarityMeasure(ABC):
    @abstractmethod
    def precompute(self, logs: List[EventLog]):
        """is called before the compute method is called. this enables to
        similarity measure to do precomputions for effeciency reasons.
        """
        pass

    @abstractmethod
    def compute(self, log1: EventLog, log2: EventLog) -> float:
        """returns a value between 0 and 1"""
        pass

    def __call__(self, log1, log2) -> float:
        return self.compute(log1,log2)

    @abstractmethod
    def is_symmetric(self) -> bool:
        pass

    def compute_similarity_matrix(self, clusters: List[EventLog]) -> np.ndarray:
        self.precompute(clusters)
        similarity_matrix = [[None for a in clusters]
                             for b in clusters]
        for i,a in enumerate(clusters):
            for j,b in enumerate(clusters):
                if i < j:
                    similarity_matrix[i][j] = self.compute(a,b)
                elif i == j:
                    similarity_matrix[i][j] = 1.0
                elif self.is_symmetric():
                    similarity_matrix[i][j] = similarity_matrix[j][i]
                else:
                    similarity_matrix[i][j] = self.compute(a,b)
        return np.array(similarity_matrix)