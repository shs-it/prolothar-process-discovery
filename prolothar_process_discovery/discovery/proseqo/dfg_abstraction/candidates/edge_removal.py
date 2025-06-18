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

import itertools

from typing import Iterable, List, Dict

import prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidate as candidate

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.cover import Cover
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.dfg.edge import Edge


from prolothar_process_discovery.discovery.proseqo.cover_streams.move_stream import MoveStream

import more_itertools

class CandidateEdgeRemoval(candidate.Candidate):
    def __init__(self, edges: Iterable[Edge]):
        super().__init__()
        self.__edge_set = frozenset(
                (edge.start.pattern,edge.end.pattern) for edge in edges)
        self.__edge_key_list = [
                (start.get_activity_name(), end.get_activity_name())
                for start,end in self.__edge_set
        ]
        self.__edges_frequency = 0
        for edge in edges:
            self.__edges_frequency += edge.count
        if len(self.__edge_key_list) > 1:
            self.__representation_string = 'remove edges: ' + ','.join(
                    '(%s,%s)' % (a,b) for a,b in self.__edge_key_list)
        else:
            self.__representation_string = 'remove edge ' + str(
                    self.__edge_key_list[0])

    def __repr__(self) -> str:
        return self.__representation_string

    def apply_on_dfg(self, dfg: PatternDfg):
        for start_pattern, end_pattern in self.__edge_set:
            for edge in itertools.product(
                    start_pattern.end_activities(),
                    end_pattern.start_activities()):
                dfg.remove_edge(edge)

    def __hash__(self) -> int:
        return hash(self.__edge_set)

    def __eq__(self, other) -> int:
        try:
            return self.__edge_set == other.__edge_set
        except AttributeError:
            return False

    def _has_conflict_with_candidate_pattern(self, other) -> bool:
        return other._has_conflict_with_candidate_edge_removal(self)

    def _has_conflict_with_candidate_edge_removal(
            self, other: 'CandidateEdgeRemoval') -> bool:
        return False

    def _has_conflict_with_candidate_node_removal(self, other) -> bool:
        return False

    def get_sort_type_int(self) -> int:
        return 0

    def estimate_cover_change(
            self, cover: Cover, pattern_dfg_before_candidate: PatternDfg,
            dfg: DirectlyFollowsGraph, add_log_moves: bool = True) -> PatternDfg:
        pattern_dfg = pattern_dfg_before_candidate
        for start_pattern, end_pattern in self.__edge_set:
            old_context = frozenset(pattern_dfg.get_following_activities(
                    start_pattern.get_activity_name()))
            if old_context in cover.pattern_stream.get_conditional_usage_per_pattern():
                count = pattern_dfg.get_count(start_pattern.get_activity_name(),
                                              end_pattern.get_activity_name())
                pattern_dfg.remove_edge(
                        (start_pattern.get_activity_name(),
                         end_pattern.get_activity_name()))
                new_path = pattern_dfg.compute_shortest_path(
                        start_pattern.get_activity_name(),
                        end_pattern.get_activity_name())
                if new_path:
                    self.__estimate_cover_change_for_noncutting_edge(
                            start_pattern, end_pattern, count, cover, pattern_dfg,
                            dfg, old_context, new_path)
                else:
                    self.__estimate_cover_change_for_cutting_edge(
                            start_pattern, end_pattern, count, old_context, cover,
                            pattern_dfg, dfg)
        return pattern_dfg

    def __estimate_cover_change_for_noncutting_edge(
            self, start_pattern: Pattern, end_pattern: Pattern, count: int,
            cover: Cover, pattern_dfg: PatternDfg, dfg: DirectlyFollowsGraph,
            old_context: frozenset[str], new_path: List[str]):
        new_context = old_context.difference([end_pattern.get_activity_name()])
        cover.pattern_stream.remove(end_pattern, old_context, count = count)
        for pattern_name in new_context:
            subcount = pattern_dfg.get_count(
                    start_pattern.get_activity_name(), pattern_name)
            cover.pattern_stream.add(
                    pattern_dfg.nodes[pattern_name].pattern,
                    new_context, count = subcount,
                    add_to_cache = False)
            cover.pattern_stream.remove(
                    pattern_dfg.nodes[pattern_name].pattern,
                    new_context, count = subcount)

        subcounts = {}
        for a in start_pattern.end_activities():
            subcounts_a = {}
            subcounts[a] = subcounts_a
            for b in end_pattern.start_activities():
                subcounts_a[b] = dfg.get_count(a, b)

        for last_covered_activity, activity_counts in subcounts.items():
            for subcount in activity_counts.values():
                i = 0
                for a,b in more_itertools.pairwise(new_path):
                    cover.pattern_stream.add(
                            pattern_dfg.nodes[b].pattern,
                            frozenset(pattern_dfg.get_following_activities(a)),
                            count = subcount, add_to_cache = False)
                    if i > 0:
                        cover.move_stream.add_model_move(
                            last_covered_activity, count = subcount,
                            add_to_cache = False)
                    i += 1

    def __estimate_cover_change_for_cutting_edge(
            self, start_pattern: Pattern, end_pattern: Pattern , count: int,
            old_context: frozenset[str], cover, pattern_dfg: PatternDfg,
            dfg: DirectlyFollowsGraph):
        all_activities = frozenset(dfg.nodes.keys())

        #remove the synchronous moves in pattern stream from start_pattern
        #to end_pattern
        cover.pattern_stream.remove(end_pattern, old_context, count = count)

        remaining_following_pattern_names = pattern_dfg.get_following_activities(
                        start_pattern.get_activity_name())
        remaining_following_patterns = [
                pattern_dfg.nodes[a].pattern
                for a in remaining_following_pattern_names]
        remaining_following_activities = set()
        for remaining_following_pattern in remaining_following_patterns:
            remaining_following_activities.update(
                    remaining_following_pattern.get_activity_set())

        #We have to make log moves from start_pattern to end_pattern
        log_move_context = all_activities.difference(remaining_following_activities)
        for start_pattern_activity in start_pattern.end_activities():
            for end_pattern_activity in end_pattern.start_activities():
                subcount = dfg.get_count(start_pattern_activity,
                                         end_pattern_activity)
                cover.move_stream.flip_moves(
                    start_pattern_activity, MoveStream.SYNCHRONOUS_MOVE,
                    MoveStream.LOG_MOVE, amount = subcount)
                cover.pattern_stream.add(
                        Singleton(end_pattern_activity), log_move_context,
                        add_to_cache = False, count = subcount)

        #if A -> B is removed, A -> C becomes cheaper
        if remaining_following_patterns:
            cover.pattern_stream.remove_pattern_from_context(
                    old_context, end_pattern)

    def estimate_cover_change_for_lower_bound(
            self, cover: Cover, pattern_dfg_before_candidate: PatternDfg,
            dfg: DirectlyFollowsGraph, add_log_moves: bool = True) -> PatternDfg:
        pattern_dfg = pattern_dfg_before_candidate
        for start_pattern, end_pattern in self.__edge_set:
            old_context = frozenset(pattern_dfg.get_following_activities(
                    start_pattern.get_activity_name()))
            new_context = old_context.difference([end_pattern.get_activity_name()])
            if old_context in cover.pattern_stream.get_conditional_usage_per_pattern():
                count = pattern_dfg.get_count(start_pattern.get_activity_name(),
                                              end_pattern.get_activity_name())

                for activity in start_pattern.end_activities():
                    cover.move_stream.decrease_count(
                        activity, cover.move_stream.SYNCHRONOUS_MOVE, count)
                if len(old_context) == 1 \
                or len(pattern_dfg.get_preceeding_activities(
                        end_pattern.get_activity_name())) == 1:
                    cover.pattern_stream.add(
                        Singleton(next(iter(end_pattern.start_activities()))),
                        cover.activity_set, count = count, add_to_cache=False)
                else:
                    cover.pattern_stream.add(
                        pattern_dfg.nodes[(next(iter(new_context)))].pattern,
                        new_context, count = count, add_to_cache=False)
                if add_log_moves:
                    cover.move_stream.add_log_move(
                        next(iter(start_pattern.end_activities())),
                        count = count,
                        add_to_cache=False)
                    if not pattern_dfg_before_candidate.compute_shortest_path(
                            start_pattern.get_activity_name(),
                            end_pattern.get_activity_name(),
                            forbidden_edges=[(start_pattern.get_activity_name(),
                                              end_pattern.get_activity_name())]) \
                    and not any(pattern_dfg_before_candidate.compute_shortest_path(
                            start_pattern.get_activity_name(),
                            sink_activity,
                            forbidden_edges=[(start_pattern.get_activity_name(),
                                              end_pattern.get_activity_name())])
                            for sink_activity in pattern_dfg_before_candidate.get_sink_activities()):
                        shortest_path = None
                        for sink_activity in pattern_dfg_before_candidate.get_sink_activities():
                            path = pattern_dfg_before_candidate.compute_shortest_path(
                                end_pattern.get_activity_name(), sink_activity)
                            if shortest_path is None or len(path) < len(shortest_path):
                                shortest_path = path
                        if shortest_path is None:
                            shortest_path = []
                        cover.move_stream.add_log_move(
                            next(iter(start_pattern.end_activities())),
                            count = count * max(0, len(shortest_path) - 1),
                            add_to_cache=False)

                cover.pattern_stream.remove(end_pattern, old_context, count = count)
                for pattern_name in new_context:
                    subcount = pattern_dfg.get_count(
                            start_pattern.get_activity_name(), pattern_name)
                    cover.pattern_stream.add(
                            pattern_dfg.nodes[pattern_name].pattern,
                            new_context, count = subcount,
                            add_to_cache = False)
                    cover.pattern_stream.remove(
                            pattern_dfg.nodes[pattern_name].pattern,
                            new_context, count = subcount)
                cover.pattern_stream.get_conditional_usage_per_pattern().pop(old_context)
            pattern_dfg.remove_edge(
                    (start_pattern.get_activity_name(),
                        end_pattern.get_activity_name()))
        return pattern_dfg

    def get_frequency_priority(self, activity_supports: Dict[str, int]) -> tuple[int]:
        """less frequent edges have a lower value (= higher priority). for
        a set of edges, the sum is returned
        """
        return (-len(self.__edge_set), self.__edges_frequency)
