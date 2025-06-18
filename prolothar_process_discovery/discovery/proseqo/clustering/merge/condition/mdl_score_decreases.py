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
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score

from prolothar_process_discovery.discovery.proseqo.pattern.clustering import Clustering
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph

from typing import List

class MdlScoreDecreases(MergeCondition):

    def __init__(self):
        self.reset()

    def should_merge(self, clusters: List[EventLog]) -> bool:
        if self._log is None:
            self._init_pattern_dfg(clusters)
        current_mdl_score = compute_mdl_score(
                self._log, self._compute_folden_pdfg(clusters))
        mdl_score_decreased = current_mdl_score < self.mdl_score
        self.mdl_score = current_mdl_score
        return mdl_score_decreased

    def reset(self):
        self.mdl_score = float('inf')
        self._pattern_dfg = None
        self._log = None

    def _init_pattern_dfg(self, clusters: List[EventLog]):
        self._pattern_dfg = PatternDfg()
        self._log = EventLog()
        for cluster in clusters:
            self._pattern_dfg.read_counts_from_log(cluster)
            self._log.add_traces(cluster.traces)

    def _compute_folden_pdfg(self, clusters: List[EventLog]) -> PatternDfg:
        return self._pattern_dfg.fold({
                self.__create_clustering_pattern(clusters)])

    def __create_clustering_pattern(self, clusters: List[EventLog]) -> Clustering:
        communities = []
        trace_to_community_index_dict = {}
        for i,cluster in enumerate(clusters):
            communities.append(self.__create_subgraph(cluster))
            for trace in cluster.traces:
                trace_to_community_index_dict[trace] = i
        return Clustering(communities, trace_to_community_index_dict)

    def __create_subgraph(self, cluster: EventLog) -> SubGraph:
        return SubGraph(PatternDfg.create_from_event_log(cluster),
                        list(cluster.compute_set_of_start_activities()),
                        list(cluster.compute_set_of_end_activities()))

    def __repr__(self) -> str:
        return 'MdlScoreDecreases'






