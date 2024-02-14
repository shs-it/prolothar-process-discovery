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

import prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidate as candidate
import prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.edge_removal as edge_removal

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.cover import Cover

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

from typing import Set, Dict

class CandidateNodeRemoval(candidate.Candidate):
    def __init__(self, pattern: Pattern):
        super().__init__()
        self.__pattern_of_node = pattern

    def __repr__(self) -> str:
        return 'remove node: %s' % self.__pattern_of_node

    def apply_on_dfg(self, dfg: PatternDfg):
        for activity in self.__pattern_of_node.get_activity_set():
            if activity in dfg.nodes:
                dfg.remove_node(activity, create_connections=False)

    def get_activity_set(self) -> Set[str]:
        return self.__pattern_of_node.get_activity_set()

    def __hash__(self) -> int:
        return hash(self.__pattern_of_node)

    def __eq__(self, other) -> int:
        try:
            return self.__pattern_of_node == other.__pattern_of_node
        except AttributeError:
            return False

    def _has_conflict_with_candidate_pattern(self, other) -> bool:
        return other._has_conflict_with_candidate_node_removal(self)

    def _has_conflict_with_candidate_edge_removal(self, other) -> bool:
        return other._has_conflict_with_candidate_node_removal(self)

    def _has_conflict_with_candidate_node_removal(self, other) -> bool:
        return False

    def get_sort_type_int(self) -> int:
        return 1

    def estimate_cover_change(
            self, cover: Cover, pattern_dfg_before_candidate: PatternDfg,
            dfg: DirectlyFollowsGraph) -> PatternDfg:
        pattern_dfg = pattern_dfg_before_candidate
        node = pattern_dfg_before_candidate.nodes[
                self.__pattern_of_node.get_activity_name()]
        for edge in list(node.edges):
            pattern_dfg = edge_removal.CandidateEdgeRemoval(
                    [edge]).estimate_cover_change(cover, pattern_dfg, dfg)
        #first pattern for all traces has one choice less
        cover.pattern_stream.remove_pattern_from_context(
                frozenset(pattern_dfg_before_candidate.nodes.keys()), node.pattern)
        pattern_dfg.remove_node(node.activity)
        return pattern_dfg

    def estimate_cover_change_for_lower_bound(
            self, cover: Cover, pattern_dfg_before_candidate: PatternDfg,
            dfg: DirectlyFollowsGraph) -> PatternDfg:
        pattern_dfg = pattern_dfg_before_candidate
        node = pattern_dfg_before_candidate.nodes[
                self.__pattern_of_node.get_activity_name()]
        for edge in list(node.edges):
            pattern_dfg = edge_removal.CandidateEdgeRemoval(
                    [edge]).estimate_cover_change_for_lower_bound(
                        cover, pattern_dfg, dfg)
        #first pattern for all traces has one choice less
        cover.pattern_stream.remove_pattern_from_context(
                frozenset(pattern_dfg_before_candidate.nodes.keys()), node.pattern)
        pattern_dfg.remove_node(node.activity)
        return pattern_dfg

    def get_frequency_priority(self, activity_supports: Dict[str, int]) -> tuple[int]:
        """less frequent nodes have a lower value (= higher priority). we
        return the sum of activity supports of the activities in this node
        """
        node_frequency = 0
        for activity in self.get_activity_set():
            node_frequency += activity_supports[activity]
        return (node_frequency,)
