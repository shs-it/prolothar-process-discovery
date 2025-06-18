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

from prolothar_common.models.eventlog import EventLog, Trace

import prolothar_common.mdl_utils as mdl_utils

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.cover_streams.pattern_stream import PatternStream
from prolothar_process_discovery.discovery.proseqo.cover_streams.meta_stream import MetaStream
from prolothar_process_discovery.discovery.proseqo.cover_streams.move_stream import MoveStream

from typing import Set

from more_itertools import pairwise

class Cover:
    def __init__(self, pattern_dfg: PatternDfg, activity_set: Set[str],
                 store_patterns_in_pattern_stream: bool = False):
        possible_patterns = [Singleton(a) for a in activity_set]
        for node in pattern_dfg.get_nodes():
            if not node.pattern.is_singleton():
                possible_patterns.append(node.pattern)
        self.pattern_stream = PatternStream(
                store_patterns=store_patterns_in_pattern_stream)
        self.meta_stream = MetaStream()
        self.move_stream = MoveStream()
        self.pattern_dfg = pattern_dfg
        self.activity_set = frozenset(activity_set)
        self.__current_trace = None
        self.__covered_activity_lists = set()
        self.__following_activities_cache = {}
        self.__all_pdfg_activity_names = frozenset(pattern_dfg.nodes.keys())

    def copy_counts_only(self) -> 'Cover':
        """returns a copy of this Cover object. Only the counts are copied.
        All caches and any other information is not copied
        """
        copy = Cover(self.pattern_dfg, self.activity_set)
        copy.move_stream = self.move_stream.copy_counts_only()
        copy.pattern_stream = self.pattern_stream.copy_counts_only()
        copy.meta_stream = self.meta_stream.copy_counts_only()
        return copy

    def get_encoded_length_of_cover(self, log: EventLog, verbose=False) -> float:
        """returns length of pattern stream + length of metrastream +
        L_N(nr_of_traces) + encoding for length of traces"""
        encoded_length = self.pattern_stream.get_code_length(verbose=verbose)
        encoded_length += self.meta_stream.get_code_length(verbose=verbose)
        encoded_length += self.move_stream.get_encoded_length(verbose=verbose)
        if verbose:
            print('encoded length of streams: %.2f' % encoded_length)
        encoded_length += mdl_utils.L_N(log.get_nr_of_traces())
        for trace in log.traces:
            encoded_length +=  mdl_utils.L_N(len(trace))
        if verbose:
            print('encoded length of cover: %.2f' % encoded_length)
        return encoded_length

    def add_log_move(self, last_covered_activity, activity_to_cover: str,
                     model_available_activities: Set[str]):
        """adds a log move to this cover. delegates calls to the move stream and
        the pattern stream of this cover"""
        self.move_stream.add_log_move(last_covered_activity)
        if model_available_activities:
            self.pattern_stream.add(
                    Singleton(activity_to_cover),
                    # a log move cannot be a model available move
                    self.activity_set.difference(model_available_activities))
        else:
            self.pattern_stream.add(
                    Singleton(activity_to_cover),
                    # a log move cannot be a model available move
                    self.activity_set)

    def add_skipped_pattern(self, pattern: Pattern, preceding_pattern: Pattern,
                            last_covered_activity: str):
        """adds codes to the streams of the cover for skipping the given pattern"""
        if preceding_pattern is not None:
            alternative_patterns = \
                self.get_following_activities(preceding_pattern.get_activity_name())
        else:
            alternative_patterns = self.__all_pdfg_activity_names

        self.pattern_stream.add(pattern, alternative_patterns)
        pattern.for_covering(
                self.__current_trace, last_covered_activity).skip_to_end(
                self, self.__current_trace, last_covered_activity)

    def get_all_pattern_names(self) -> str:
        return self.__all_pdfg_activity_names

    def get_following_activities(self, activity: str) -> frozenset[str]:
        """
        for one high-level activity returns the following activities in the
        pattern graph of this cover. this method speeds up repetitive requests
        with a cache
        """
        try:
            return self.__following_activities_cache[activity]
        except KeyError:
            following_activities = frozenset(
                 self.pattern_dfg.get_following_activities(activity))
            self.__following_activities_cache[activity] = following_activities
            return following_activities

    def start_trace_covering(self, trace: Trace):
        """signal that now the given trace starts to get covered"""
        self.__current_trace = trace
        activity_list = tuple(trace.to_activity_list())
        if activity_list in self.__covered_activity_lists:
            raise ValueError(
                    'covering steps in cache. use "use_cache_to_cover_trace"')
        self.pattern_stream.start_trace_covering(activity_list)
        self.meta_stream.start_trace_covering(activity_list)
        self.move_stream.start_trace_covering(activity_list)

    def end_trace_covering(self, trace: Trace):
        """signal that now the given trace is get covered"""
        self.__current_trace = None
        activity_list = tuple(trace.to_activity_list())
        self.pattern_stream.end_trace_covering(activity_list)
        self.meta_stream.end_trace_covering(activity_list)
        self.move_stream.end_trace_covering(activity_list)
        self.__covered_activity_lists.add(activity_list)

    def can_cover_trace_with_cache(self, trace: Trace) -> bool:
        """returns True if a trace with the same activity sequence already
        has been covered"""
        return tuple(trace.to_activity_list()) in self.__covered_activity_lists

    def use_cache_to_cover_trace(self, trace: Trace):
        """repeats the addition of codes as it is stored in a cache for the
        same sequence of activities as the given trace"""
        activity_list = tuple(trace.to_activity_list())
        self.pattern_stream.use_cache_to_cover_trace(activity_list)
        self.meta_stream.use_cache_to_cover_trace(activity_list)
        self.move_stream.use_cache_to_cover_trace(activity_list)

    def get_activity_set(self) -> Set[str]:
        """returns the activity set = singletons"""
        return self.activity_set

    def get_pattern_dfg_with_restored_counts(self) -> PatternDfg:
        """first, sets all counts of the PatternDfg to 0.
        Then, the pattern stream is used to set counts in the graph.
        This is only allowed, if store_patterns_in_pattern_stream was set to
        true. Otherwise a ValueError is thrown.
        """
        pattern_dfg = self.pattern_dfg.copy()
        sources = pattern_dfg.get_source_activities()

        for edge in pattern_dfg.get_edges():
            edge.count = 0

        last_working_edge = None
        for pattern_a, pattern_b in pairwise(
                self.pattern_stream.get_sequence_of_added_patterns()):
            edge = (pattern_a.get_activity_name(), pattern_b.get_activity_name())
            if edge not in pattern_dfg.edges and last_working_edge:
                #we had a log move => connect to last non-move activity
                edge = (last_working_edge[1], edge[1])
            if edge in pattern_dfg.edges:
                pattern_dfg.add_count(edge[0], edge[1])
                last_working_edge = edge
            #if we are at the end of a trace
            if edge[1] in sources:
                last_working_edge = edge

        return pattern_dfg