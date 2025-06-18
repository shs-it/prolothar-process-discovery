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
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.clustering import Clustering
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_common.models.eventlog import EventLog, Trace

from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import find_isolated_sequences_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_loops import find_isolated_loops_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_choices import find_one_step_choices_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_optionals import find_one_step_optionals_in_dfg

from typing import List, Dict, Callable

def create_pattern_dfg_from_clusters(
        clusters: List[EventLog],
        cluster_compressor: Callable[[PatternDfg],
                                     PatternDfg] = None) -> PatternDfg:
    pattern_dfg = PatternDfg()
    clustering_pattern = Clustering(
            [create_subgraph_from_cluster(
                    cluster, cluster_compressor = cluster_compressor)
             for cluster in clusters],
            create_trace_to_community_dict(clusters))
    pattern_dfg.add_node(clustering_pattern.get_activity_name())
    pattern_dfg.add_pattern(clustering_pattern.get_activity_name(),
                            clustering_pattern)
    return pattern_dfg

def create_subgraph_from_cluster(
        cluster: EventLog,
        cluster_compressor: Callable[[PatternDfg],
                                     PatternDfg] = None) -> SubGraph:
    pattern_dfg = PatternDfg.create_from_event_log(cluster)
    if cluster_compressor is not None:
        pattern_dfg = cluster_compressor(pattern_dfg)

    pattern_dfg_start_activities = set()
    for start_activity in cluster.compute_set_of_start_activities():
        if start_activity in pattern_dfg.nodes:
            pattern_dfg_start_activities.add(start_activity)
        else:
            for pattern in pattern_dfg.get_patterns_with_activity(start_activity):
                pattern_dfg_start_activities.add(pattern.get_activity_name())

    pattern_dfg_end_activities = set()
    for end_activity in cluster.compute_set_of_end_activities():
        if end_activity in pattern_dfg.nodes:
            pattern_dfg_end_activities.add(end_activity)
        else:
            for pattern in pattern_dfg.get_patterns_with_activity(end_activity):
                pattern_dfg_end_activities.add(pattern.get_activity_name())

    return SubGraph(pattern_dfg,
                    pattern_dfg_start_activities,
                    pattern_dfg_end_activities).without_degeneration()[0]

def create_trace_to_community_dict(clusters: List[EventLog]) -> Dict[Trace,int]:
    trace_to_community_dict = {}
    for i,community_log in enumerate(clusters):
        for trace in community_log.traces:
            trace_to_community_dict[trace] = i
    return trace_to_community_dict

def compress_with_simple_patterns(pattern_dfg: PatternDfg) -> PatternDfg:
    change = True
    while change:
        change = False
        for pattern_finder in [
                find_isolated_sequences_in_dfg,
                find_isolated_loops_in_dfg,
                find_one_step_choices_in_dfg,
                find_one_step_optionals_in_dfg]:
            patterns = pattern_finder(pattern_dfg)
            if patterns:
                pattern_dfg = pattern_dfg.fold(set(patterns))
                change = True
    return pattern_dfg