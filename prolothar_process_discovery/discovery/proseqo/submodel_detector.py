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
from prolothar_common.models.eventlog import EventLog

from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.closed_communities import find_closed_communities_in_dfg
from prolothar_process_discovery.discovery.proseqo.clustering.clustering_strategy import ClusteringStrategy
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.pattern.clustering import Clustering

from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score

from typing import List, Union

class SubmodelDetector():
    """part of the proseqo algorithm that detects necessary submodels = subgraphs
    and clustering"""

    def __init__(self, clustering_strategies: List[ClusteringStrategy]):
        self.__clustering_strategies = clustering_strategies

    def detect(self, pattern_dfg: PatternDfg, log: EventLog,
               verbose: bool = False):
        communities = find_closed_communities_in_dfg(pattern_dfg)

        clustered_communities = []
        sub_pattern_dfgs = []
        for community in communities:
            clustered_community, submodel_partition = \
                self.__cluster_community(community, log, verbose)
            clustered_communities.append(clustered_community)
            sub_pattern_dfgs.extend(submodel_partition)
        if len(clustered_communities) > 1 or (len(clustered_communities) == 1
                                    and isinstance(clustered_communities[0],
                                                   Clustering)):
            return pattern_dfg.fold(clustered_communities), sub_pattern_dfgs
        else:
            return pattern_dfg, []

    def __cluster_community(self, community: SubGraph, log: EventLog,
                            verbose: bool) -> Union[SubGraph,Clustering]:
        sublog = community.create_cut_log_from_community(log)

        one_cluster = community.pattern_dfg.fold({
                self.__create_clustering_pattern([sublog])])
        best_mdl = compute_mdl_score(sublog, one_cluster, verbose=False)
        best_pattern = community
        best_submodel_partition = [(community, sublog)]

        for clustering_strategy in self.__clustering_strategies:
            cluster = self.__create_clustering_pattern(
                    clustering_strategy.cluster(sublog))
            mdl_with_cluster = compute_mdl_score(
                    sublog, community.pattern_dfg.fold({cluster]), verbose=False)
            if mdl_with_cluster < best_mdl:
                if verbose:
                    print('%r with %d clusters could improve MDL (%.2f < %.2f)' % (
                            clustering_strategy, cluster.get_nr_of_subpatterns(),
                            mdl_with_cluster, best_mdl))
                best_mdl = mdl_with_cluster
                best_pattern = cluster
                best_submodel_partition = [
                    (c, cluster.get_sublog_for_community_index(i))
                    for i,c in enumerate(cluster.communities)]
            elif verbose:
                print('%r with %d clusters could not improve MDL (%.2f >= %.2f)' % (
                        clustering_strategy, cluster.get_nr_of_subpatterns(),
                        mdl_with_cluster, best_mdl))

        return best_pattern, best_submodel_partition

    def __create_clustering_pattern(self, clusters: List[EventLog]) -> Clustering:
        trace_to_community_index_dict = {}
        for i,cluster in enumerate(clusters):
            for trace in cluster.traces:
                trace_to_community_index_dict[trace] = i
        return Clustering([
                SubGraph(
                        PatternDfg.create_from_event_log(subsublog),
                        subsublog.compute_set_of_start_activities(),
                        subsublog.compute_set_of_end_activities())
                for subsublog in clusters], trace_to_community_index_dict)
