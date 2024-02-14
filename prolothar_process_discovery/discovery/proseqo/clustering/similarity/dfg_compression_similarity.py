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
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.similarity_measure import SimilarityMeasure
from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_size.pattern_dfg_size import PatternDfgSize
from prolothar_process_discovery.discovery.proseqo.clustering.mdl_clustering_utils import compress_with_simple_patterns

from typing import List

class DfgCompressionSimilarity(SimilarityMeasure):
    """similarity measure that is based on Normalized Compression Distance
    as defined by Cilibrasi and Vitanyi in "Clustering by Compression" 2005.

    The normalized compression similarity NCS(x,y) of two logs is computed by

    NCS(x,y) := 1 - NCD(x,y)

    NCD(x,y) := (C(x,y) - min{C(x), C(y)}) / max{C(x), C(y)}
    """

    def __init__(self, pattern_dfg_size: PatternDfgSize,
                 compress_pattern_dfg: bool = False):
        self.pattern_dfg_size = pattern_dfg_size
        self.compress_pattern_dfg = compress_pattern_dfg

    def precompute(self, logs: List[EventLog]):
        self.pattern_dfg_size.precompute(logs)
        for log in logs:
            log.size = self._compute_log_size(log)

    def compute(self, log1: EventLog, log2: EventLog) -> float:
        concatenated_log = EventLog()
        concatenated_log.add_traces(log1.traces)
        concatenated_log.add_traces(log2.traces)

        concatenated_size = self._compute_log_size(concatenated_log)

        return min(1, 1 - ((concatenated_size - min(log1.size, log2.size)) /
                    max(log1.size, log2.size)))

    def _compute_log_size(self, log: EventLog):
        pattern_dfg = PatternDfg.create_from_event_log(log)
        if self.compress_pattern_dfg:
            pattern_dfg = compress_with_simple_patterns(pattern_dfg)
        return self.pattern_dfg_size.compute_size(pattern_dfg)

    def is_symmetric(self) -> bool:
        return True

    def __repr__(self) -> str:
        return 'DfgCompressionSimilarity<%r>' % self.pattern_dfg_size

