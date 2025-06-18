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

from typing import List, Dict, Tuple, Set

from prolothar_common import mdl_utils
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_common.models.eventlog import EventLog, Trace
from prolothar_common.models.dfg.node import Node

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Place
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import NR_OF_PATTERN_TYPES_WITH_SINGLETON

from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_clustering import CoveringClustering

from math import log2
from random import Random

from collections import Counter

class Clustering(Pattern):
    def __init__(self, communities: List[Pattern],
                 trace_to_community_index_dict: Dict[Trace, int]):
        super().__init__()
        self.communities = communities
        self.trace_to_community_index_dict = trace_to_community_index_dict
        if len(self.communities) > len(self.trace_to_community_index_dict):
            raise ValueError(
                    'nr of communities %d is larger than the number of traces %d' % (
                    len(self.communities), len(self.trace_to_community_index_dict)))

    def expand_dfg(self, node: Node, dfg, recursive: bool = True):
        raise NotImplementedError()

    def fold_dfg(self, dfg: DirectlyFollowsGraph):
        all_activities = _find_activities(dfg, self.communities)

        preceeding_activities = self._compute_preceeding_activities(
                all_activities, dfg)

        following_activities = self._compute_following_activities(
                all_activities, dfg)

        for activity in all_activities:
            dfg.remove_node(activity)

        for activity in preceeding_activities:
            dfg.add_count(activity, self.get_activity_name())

        for activity in following_activities:
            dfg.add_count(self.get_activity_name(), activity)

        #if the cluster spans over the whole dfg, then there are no
        #preceeding or following activities and thus we have removed all
        #nodes => we add the cluster as the single node in the graph
        if dfg.get_nr_of_nodes() == 0:
            dfg.add_node(self.get_activity_name())

        dfg.nodes[self.get_activity_name()].pattern = self

    def _compute_preceeding_activities(self, all_activities, dfg):
        preceeding_activities = set()
        for activity in all_activities:
            for predecessor in dfg.get_preceeding_activities(activity):
                if predecessor not in all_activities:
                    preceeding_activities.add(predecessor)
        return preceeding_activities

    def _compute_following_activities(self, all_activities, dfg):
        following_activities = set()
        for activity in all_activities:
            for ancestor in dfg.get_following_activities(activity):
                if ancestor not in all_activities:
                    following_activities.add(ancestor)
        return following_activities

    def get_start_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def get_end_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def _generate_activity_name(self) -> str:
        return '(' + '|'.join(c.get_activity_name() for c in self.communities) +  ')'

    def get_nr_of_subpatterns(self) -> int:
        return len(self.communities)

    def get_subpatterns(self) -> List[Pattern]:
        return self.communities

    def get_encoded_length_in_code_table(
            self, available_activities: Set[str]) -> Tuple[float,Set[str]]:
        #encode nr of subpatterns (len(activities) is an upper bound)
        code_length = log2(len(available_activities))
        #types of the subpatterns including singleton
        code_length += len(self.communities) * log2(NR_OF_PATTERN_TYPES_WITH_SINGLETON)
        #how many traces contains each submodel
        code_length += mdl_utils.L_U(
                len(self.trace_to_community_index_dict), len(self.communities))
        #which trace belongs to which submodel?
        code_length += mdl_utils.log2multinom(
                len(self.trace_to_community_index_dict),
                self.__get_nr_of_traces_per_community())
        #encoding of subpatterns
        for pattern in self.communities:
            code_length += pattern.get_encoded_length_in_code_table(
                    available_activities)[0]
        return code_length, available_activities

    def __get_nr_of_traces_per_community(self) -> List[int]:
        return [v for v in Counter(
                self.trace_to_community_index_dict.values()).values()]

    def for_covering(self, trace, last_covered_activity: str):
        return CoveringClustering(self, trace, last_covered_activity)

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str):
        nr_of_nodes = 0
        for pattern in self.get_subpatterns():
            pattern_id = base_id + '.' + str(nr_of_nodes)
            graph.add_node(pattern.create_node_for_nested_graph(
                    pattern_id, parent_id=base_id))
            pattern.add_subpatterns_to_nested_graph(graph, pattern_id)
            nr_of_nodes += 1

    def _without_degeneration(self) -> Tuple[Pattern, bool]:
        """ a clustering is degenerated if there is only one cluster
        """
        if self.get_nr_of_subpatterns() == 1:
            return self.get_subpatterns()[0].without_degeneration()[0], True
        else:
            subpatterns_without_degeneration = [
                    c.without_degeneration() for c in self.communities]
            changed = any(s[1] for s in subpatterns_without_degeneration)
            if changed:
                self.communities = [
                    s[0] for s in subpatterns_without_degeneration]
            return self, changed

    def _merge_subpatterns(self):
        changed = False
        for community in self.communities:
            if community.merge_subpatterns():
                changed = True
            if isinstance(community, Clustering):
                raise NotImplementedError()
        return changed

    def _remove_activity(self, activity: str):
        changed = False
        for cluster in self.communities:
            if cluster.remove_activity(activity):
                changed = True
        return changed

    def get_cluster_for_trace(self, trace: Trace) -> Pattern:
        """returns the subpattern (=cluster) of this clustering for the given
        trace"""
        return self.communities[self.trace_to_community_index_dict[trace]]

    def get_sublog_for_community_index(self, community_index: int):
        """returns the event log with traces that are assigned to the cluster
        with the given index"""
        sublog = EventLog()
        for trace, trace_community_index in self.trace_to_community_index_dict.items():
            if trace_community_index == community_index:
                sublog.add_trace(trace)
        return sublog

    def _copy(self) -> 'Pattern':
        return Clustering(
                [subpattern.copy() for subpattern in self.get_subpatterns()],
                dict(self.trace_to_community_index_dict))

    def add_to_petri_net(self, petri_net: DataPetriNet) -> Tuple[Place,Place]:
        raise NotImplementedError('clustering does not support petri nets')

    def _replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        self.communities = [subpattern.replace_singleton(activity, pattern)
                            for subpattern in self.communities]
        return self

    def _replace_direct_subpattern(self, subpattern: 'Pattern',
                                   replacement: 'Pattern'):
        self.communities[self.communities.index(subpattern)] = replacement

    def get_nr_of_forbidden_edges_in_pattern_dfg(self, pattern_dfg) -> int:
        return 0

    def _start_activities(self) -> Set[str]:
        start_activities = set()
        for cluster in self.communities:
            start_activities.update(cluster.start_activities())
        return start_activities

    def _end_activities(self) -> Set[str]:
        end_activities = set()
        for cluster in self.communities:
            end_activities.update(cluster.end_activities())
        return end_activities

    def generate_activities(self, random: Random = None) -> List[str]:
        if random is None:
            random = Random()
        return random.choice(self.communities).generate_activities(random)

def _find_activities(dfg, subpatterns):
    activities = set()
    for subpattern in subpatterns:
        activity_name = subpattern.get_activity_name()
        if activity_name in dfg.nodes:
            activities.add(activity_name)
        else:
            #the clustered communities can have reconstructed patterns that do
            #not match the order of subactities in the activity names (e.g. for choices)
            #=> as a very ugly workaround, we use our convention that each high level pattern
            #must have a unique activity set
            if isinstance(dfg, PatternDfg):
                matching_patterns = dfg.get_patterns_with_activity(
                        next(iter(subpattern.get_activity_set())))
                if matching_patterns:
                    activities.add(matching_patterns[0].get_activity_name())
            #high level pattern is not in dfg, but maybe its subpatterns
            activities = activities.union(_find_activities(
                    dfg, subpattern.get_subpatterns()))
    return activities