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

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.dfg.node import Node
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from typing import Set

def find_closed_communities_in_dfg(dfg: DirectlyFollowsGraph) -> Set[SubGraph]:
    original_dfg = dfg.copy()
    dfg = dfg.copy()
    source_candidates = [node for node in dfg.get_nodes() if dfg.compute_indegree(node.activity) == 0]
    communities = []
    while source_candidates:
        community_dfg = _create_community_dfg(source_candidates.pop(), dfg)

        source_activities = community_dfg.get_source_activities()
        sink_activities = community_dfg.get_sink_activities()

        if source_activities and sink_activities:
            community = SubGraph(community_dfg, source_activities, sink_activities)

            communities.append(community)

            _remove_community(dfg, community)

            _remove_intermediate_added_source_node_if_necessary(community)

            source_candidates = [node for node in dfg.get_nodes() if dfg.compute_indegree(node.activity) == 0]
        else:
            source_candidates = []

    if isinstance(original_dfg, PatternDfg):
        _take_patterns_from_original_dfg(original_dfg, communities)

    return communities

def _is_closed_community(community: PatternDfg, dfg: DirectlyFollowsGraph):
    sink_activities = set(map(lambda n: n.activity, community.get_sink_nodes()))
    all_activities = set(map(lambda n: n.activity, community.get_nodes()))

    if len(sink_activities) != 1:
        return False

    for activity in all_activities:
        for preceeding_activity in dfg.get_preceeding_activities(activity):
            if preceeding_activity not in community.nodes:
                return False

    for activity in all_activities.difference(sink_activities):
        for following_activity in dfg.get_following_activities(activity):
            if following_activity not in community.nodes:
                return False

    return True

def _extend_community(community: PatternDfg, dfg: DirectlyFollowsGraph) -> bool:
    could_extend = False

    sink_activities = set(map(lambda n: n.activity, community.get_sink_nodes()))
    all_activities = set(map(lambda n: n.activity, community.get_nodes()))

    if len(all_activities) == 1:
        activity = community.get_source_nodes()[0].activity
        could_extend = could_extend or _add_following_activities(
                community, dfg, activity)

    for activity in all_activities:
        could_extend = could_extend or _add_preceeding_activities(
                community, dfg, activity)

    for activity in all_activities:
        if (activity not in sink_activities or
            len(dfg.get_preceeding_activities(activity)) > 0):
            could_extend = could_extend or _add_following_activities(
                    community, dfg, activity)

    return could_extend

def _add_preceeding_activities(community, dfg, activity):
    could_extend = False
    for preceeding_activity in dfg.get_preceeding_activities(activity):
        if (preceeding_activity, activity) not in community.edges:
            community.add_count(preceeding_activity, activity)
            could_extend = True
    return could_extend

def _add_following_activities(community, dfg, activity):
    could_extend = False
    for following_activity in dfg.get_following_activities(activity):
        if (activity, following_activity) not in community.edges:
            community.add_count(activity, following_activity)
            could_extend = True
            _add_preceeding_activities(community, dfg, following_activity)
    return could_extend

def _insert_missing_intra_connections(community: PatternDfg,
                                      dfg: DirectlyFollowsGraph):
    for node in community.get_nodes():
        for activity in dfg.get_following_activities(node.activity):
            if ((node.activity, activity) not in community.edges and
                activity in community.nodes):
                community.add_count(node.activity, activity)

def _remove_community(dfg: DirectlyFollowsGraph, community: PatternDfg):
    for activity in community.get_activity_set():
        if (len(community.pattern_dfg.get_following_activities(activity)) == 0 and
            len(dfg.get_following_activities(activity)) > 1):
            dfg.add_node(activity + '*#!')
            for following_activity in dfg.get_following_activities(activity):
                dfg.add_count(activity + '*#!', following_activity)

        dfg.remove_node(activity)

def _take_patterns_from_original_dfg(original_dfg, communities):
    for community in communities:
        for node in community.pattern_dfg.get_nodes():
            node.pattern = original_dfg.nodes[node.pattern.activity].pattern

def _create_community_dfg(source: Node, dfg: DirectlyFollowsGraph):
    community = PatternDfg()
    community.add_node(source.activity)
    while ((not _is_closed_community(community, dfg) or
            community.get_nr_of_nodes() == 1) and
            community.get_nr_of_nodes() < dfg.get_nr_of_nodes()):
        if not _extend_community(community, dfg):
            break
        _insert_missing_intra_connections(community, dfg)
    return community

def _remove_intermediate_added_source_node_if_necessary(
        community: SubGraph):
    source_activities = community.pattern_dfg.get_source_activities()
    if len(source_activities) == 1 and source_activities[0].endswith('*#!'):
          new_start_activities = community.pattern_dfg.get_following_activities(
                  source_activities[0])
          community.pattern_dfg.remove_node(source_activities[0])
          community.set_start_activities(new_start_activities)
