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
import prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.node_removal as node_removal

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.cover import Cover

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

from typing import Tuple, Dict

class CandidatePattern(candidate.Candidate):
    def __init__(self, pattern: Pattern):
        super().__init__()
        self.__pattern = pattern


    def __repr__(self) -> str:
        return 'pattern: %r' % self.__pattern

    def apply_on_dfg(self, dfg: PatternDfg):
        self.__pattern.fold_dfg(dfg)

    def __hash__(self) -> int:
        return hash(self.__pattern)

    def __eq__(self, other) -> int:
        try:
            return self.__pattern == other.__pattern
        except AttributeError:
            return False

    def get_pattern(self) -> Pattern:
        return self.__pattern

    def _has_conflict_with_candidate_pattern(
            self, other: 'CandidatePattern') -> bool:
        return self.get_pattern().get_activity_set(
                ).intersection(other.get_pattern().get_activity_set())

    def _has_conflict_with_candidate_edge_removal(
            self, other: edge_removal.CandidateEdgeRemoval) -> bool:
        return False

    def _has_conflict_with_candidate_node_removal(
            self, other: node_removal.CandidateNodeRemoval) -> bool:
        return self.__pattern.get_activity_set().intersection(
                    other.get_activity_set())

    def get_sort_type_int(self) -> Tuple:
        return 2

    def estimate_cover_change(
            self, cover: Cover, pattern_dfg_before_candidate: PatternDfg,
            dfg: DirectlyFollowsGraph,
            edge_removal_estimator = edge_removal.CandidateEdgeRemoval.estimate_cover_change,
            consider_loopy_edges: bool = False) -> PatternDfg:
        pattern_dfg = pattern_dfg_before_candidate.copy()

        for node in list(pattern_dfg_before_candidate.get_nodes()):
            if node.pattern.get_activity_set().intersection(
                    self.__pattern.get_activity_set()):
                node.pattern.expand_dfg(node, pattern_dfg)
        self.__pattern.fold_dfg(pattern_dfg)

        # choice at first step is reduced
        conditional_usage_per_pattern = \
            cover.pattern_stream.get_conditional_usage_per_pattern()
        old_context = frozenset(pattern_dfg_before_candidate.nodes.keys())
        original_patterns = old_context.difference(pattern_dfg.nodes.keys())
        new_context = frozenset(pattern_dfg.nodes.keys())
        usage_per_first_pattern = conditional_usage_per_pattern.pop(old_context)
        new_usage_per_first_pattern = {}
        for pattern in old_context:
            pattern_usage = usage_per_first_pattern[pattern]
            if pattern in original_patterns:
                new_usage_per_first_pattern[
                        self.__pattern.get_activity_name()] = pattern_usage
            else:
                new_usage_per_first_pattern[pattern] = pattern_usage
        conditional_usage_per_pattern[new_context] = new_usage_per_first_pattern

        edges_before = set(pattern_dfg_before_candidate.expand().edges.keys())
        edges_afterwards = set(pattern_dfg.expand().edges.keys())
        missing_edges = set()
        for a,b in edges_before.difference(edges_afterwards):
            a = pattern_dfg_before_candidate.get_patterns_with_activity(a)[0]
            a = a.get_activity_name()
            b = pattern_dfg_before_candidate.get_patterns_with_activity(b)[0]
            b = b.get_activity_name()
            if (a,b) in pattern_dfg_before_candidate.edges:
                missing_edges.add(pattern_dfg_before_candidate.edges[(a,b)])
        if missing_edges:
            edge_removal_estimator(
                edge_removal.CandidateEdgeRemoval(missing_edges),
                cover, pattern_dfg_before_candidate, dfg)
        #remove loop edges as a very optimistic estimate
        if consider_loopy_edges:
            loop_edges = set()
            for a in self.__pattern.start_activities():
                for b in self.__pattern.end_activities():
                    try:
                        a = pattern_dfg_before_candidate.get_patterns_with_activity(a)[0]
                        a = a.get_activity_name()
                        b = pattern_dfg_before_candidate.get_patterns_with_activity(b)[0]
                        b = b.get_activity_name()
                        if (b,a) in pattern_dfg_before_candidate.edges:
                            loop_edges.add(pattern_dfg_before_candidate.edges[(b,a)])
                    except IndexError:
                        pass
            if loop_edges:
                edge_removal_estimator(
                    edge_removal.CandidateEdgeRemoval(loop_edges),
                    cover, pattern_dfg_before_candidate, dfg,
                    add_log_moves=False)

        return pattern_dfg

    def estimate_cover_change_for_lower_bound(
            self, cover: Cover, pattern_dfg_before_candidate: PatternDfg,
            dfg: DirectlyFollowsGraph) -> PatternDfg:
        return self.estimate_cover_change(
            cover, pattern_dfg_before_candidate,
            dfg, edge_removal_estimator=edge_removal.CandidateEdgeRemoval.estimate_cover_change_for_lower_bound,
            consider_loopy_edges=True)

    def get_frequency_priority(self, activity_supports: Dict[str, int]) -> tuple[int]:
        """more frequent nodes have a lower value (= higher priority). we
        return the negative sum of activity supports of the activities in this
        pattern
        """
        pattern_frequency = 0
        for activity in self.get_pattern().get_activity_set():
            pattern_frequency += activity_supports[activity]
        #most frequent pattern first
        return (-pattern_frequency,)
