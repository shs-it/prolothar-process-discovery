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
import numpy as np
from prolothar_process_discovery.conformance.logdistance.abstract_min_edit_distance import AbstractMinEditDistance

class GreedyMinEditLogDistance(AbstractMinEditDistance):

    def _compute_distance_from_trace_distance_matrix(
            self, trace_distance_matrix) -> int:
        distance = 0
        for _ in range(trace_distance_matrix.shape[0]):
            row = trace_distance_matrix[0,:]
            min_column = np.argmin(row)
            distance += row[min_column]
            trace_distance_matrix = trace_distance_matrix[
                    1:,[i for i in range(trace_distance_matrix.shape[1])
                       if i != min_column]]
        return distance

