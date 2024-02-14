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
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

from typing import List, Set, Callable

class DfgEdgeSetSimilarity(SimilarityMeasure):
    def __init__(self, set_similarity: Callable[[Set, Set], float]):
        self.set_similarity = set_similarity

    def precompute(self, logs: List[EventLog]):
        for log in logs:
            log.dfg_edge_set = set(DirectlyFollowsGraph.create_from_event_log(
                    log).edges.keys())

    def compute(self, log1: EventLog, log2: EventLog) -> float:
        return self.set_similarity(log1.dfg_edge_set, log2.dfg_edge_set)

    def is_symmetric(self) -> bool:
        return True

    def __repr__(self) -> str:
        return 'DfgEdgeSetSimilarity<%s>' % self.set_similarity.__name__