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

from typing import List, Set, Dict

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg, Pattern
from prolothar_process_discovery.discovery.proseqo.cover import Cover
from prolothar_common.models.eventlog import EventLog, Trace

def compute_cover(trace_list: List[Trace], pattern_dfg: PatternDfg,
                  store_patterns_in_pattern_stream: bool = False,
                  activity_set: Set[str]=None) -> Cover:
    """computes a Cover for a PatternDfg on a given list of Traces. This
    method is a convenience method that uses an instance of
    GreedyCoverComputer"""
    return GreedyCoverComputer(pattern_dfg).compute(
            trace_list,
            store_patterns_in_pattern_stream=store_patterns_in_pattern_stream,
            activity_set=activity_set)

class GreedyCoverComputer():
    """computes a Cover for a PatternDfg on a given list of Traces"""
    def __init__(self, pattern_dfg: PatternDfg):
        self.pattern_dfg = pattern_dfg
        self.cached_shortest_paths = {}
        self.cached_reachable_activities = {}
        self.cached_patterns_for_activity = \
            self.__create_cached_patterns_for_activities()
        self.__activities_in_pattern_dfg = set()
        for node in pattern_dfg.get_nodes():
            self.__activities_in_pattern_dfg.update(
                    node.pattern.get_activity_set())

    def __create_cached_patterns_for_activities(self) -> Dict[str, List[str]]:
        """returns a dictionary that stores for each activity in which
        patterns (activity names of the these patterns) this activity occurs.
        """
        cached_patterns_for_activity = {}
        for node in self.pattern_dfg.get_nodes():
            for activity in node.pattern.get_activity_set():
                if activity not in cached_patterns_for_activity:
                    cached_patterns_for_activity[activity] = []
                cached_patterns_for_activity[
                        activity].append(node.pattern)
        return cached_patterns_for_activity

    def compute(self, trace_list: List[Trace],
                store_patterns_in_pattern_stream: bool = False,
                activity_set: Set[str] = None,
                cover: Cover = None) -> Cover:
        """computes a Cover for a PatternDfg on a given list of Traces"""

        event_log = EventLog()
        event_log.traces = trace_list
        if activity_set is None:
            activity_set = event_log.compute_activity_set()

        if cover is None:
            cover = Cover(
                self.pattern_dfg, activity_set,
                store_patterns_in_pattern_stream=store_patterns_in_pattern_stream)

        for trace in trace_list:
            if cover.can_cover_trace_with_cache(trace):
                cover.use_cache_to_cover_trace(trace)
            else:
                self._extend_cover_for_trace(cover, trace)

        return cover

    def _extend_cover_for_trace(self, cover: Cover, trace: Trace):
        cover.start_trace_covering(trace)
        current_covering_pattern = None
        last_covered_activity = None
        for event in trace.events:
            next_matching_patterns = self.__get_next_matching_patterns(event)
            #if there is no pattern containing the activity, we have a log move
            if not next_matching_patterns:
                self.__add_log_move(
                        cover, current_covering_pattern,
                        last_covered_activity, event.activity_name)
            #currently, we expect that only one high-level pattern contains the activity
            elif len(next_matching_patterns) > 1:
                raise NotImplementedError(
                        'more than one matching pattern for "%s"' % event.activity_name)
            #standard case: there is exactly one pattern containing the activity
            else:
                current_covering_pattern = self.__cover_event_using_pattern(
                        current_covering_pattern, next_matching_patterns[0],
                        last_covered_activity, event, cover, trace)
            last_covered_activity = event.activity_name
        cover.end_trace_covering(trace)

    def __get_next_matching_patterns(self, event):
        try:
            return self.cached_patterns_for_activity[event.activity_name]
        except KeyError:
            #Pattern DFG does not contain activity
            return []

    def __cover_event_using_pattern(
            self, current_covering_pattern, pattern,
            last_covered_activity, event, cover, trace):
        #case 1: we are still in the same pattern and continue our cover with
        #this pattern
        if (current_covering_pattern is not None and
            pattern == current_covering_pattern.pattern):
            current_covering_pattern = self._handle_continue_pattern_in_cover(
                    current_covering_pattern, cover, trace,
                    last_covered_activity, event.activity_name)
        #case 2: we have a pattern change
        else:
            current_covering_pattern = self._handle_pattern_change_in_cover(
                    current_covering_pattern, cover, trace,
                    pattern, last_covered_activity, event.activity_name)

        return current_covering_pattern

    def _handle_continue_pattern_in_cover(
            self, current_covering_pattern: Pattern, cover: Cover,
            trace: Trace, last_covered_activity: str,
            next_activity_to_cover: str) -> Pattern:
        #if we are already at the end of the current pattern, we have to repeat it.
        #however, we are only allowed to do this iff there is a self-loop
        if current_covering_pattern.completed_covering:
            following_activities = cover.get_following_activities(
                    current_covering_pattern.pattern.get_activity_name())
            current_covering_pattern = current_covering_pattern.pattern.for_covering(
                trace,
                current_covering_pattern.last_covered_activity_before_this_pattern)
            if (current_covering_pattern.pattern.get_activity_name() in
                following_activities):
                cover.pattern_stream.add(current_covering_pattern.pattern,
                                         following_activities)
                current_covering_pattern.process_covering_step(
                    cover,
                    current_covering_pattern.last_covered_activity_before_this_pattern,
                    next_activity_to_cover)
            else:
                self.__add_log_move(cover, current_covering_pattern,
                                    last_covered_activity,
                                    next_activity_to_cover,
                                    caused_by_non_existing_loop=True)
        else:
            current_covering_pattern.process_covering_step(
                    cover, last_covered_activity, next_activity_to_cover)
        return current_covering_pattern

    def _handle_pattern_change_in_cover(
            self, current_covering_pattern: Pattern, cover: Cover,
            trace: Trace, next_matching_pattern: Pattern,
            last_covered_activity: str,
            next_activity_to_cover: str) -> Pattern:
        """
            1. first we have to finish covering with current pattern by using skip events
            2. if we have intermediate patterns between the two patterns in the
               pattern dfg, then we have to skip them (model moves)
            3. then we can start to use the next pattern
            Exception: there is no path between the two patterns => log move
        """
        if current_covering_pattern is not None:
            shortest_path = self._get_shortest_path(
                    cover,
                    current_covering_pattern.pattern,
                    next_matching_pattern)
            if shortest_path:
                current_covering_pattern.skip_to_end(
                    cover, trace, last_covered_activity)

                self._skip_intermediate_patterns(
                        cover, last_covered_activity,
                        current_covering_pattern.pattern, shortest_path[1:-1])
                next_current_covering_pattern = next_matching_pattern.for_covering(
                        trace, last_covered_activity)
                cover.pattern_stream.add(
                        next_current_covering_pattern.pattern,
                        cover.get_following_activities(shortest_path[-2]))
                next_current_covering_pattern.process_covering_step(
                        cover, last_covered_activity, next_activity_to_cover)
            else:
                self.__add_log_move(cover, current_covering_pattern,
                                    last_covered_activity, next_activity_to_cover)
                return current_covering_pattern
        else:
            #we are at the start of the trace
            next_current_covering_pattern = next_matching_pattern.for_covering(
                    trace, None)
            next_current_covering_pattern.process_covering_step(
                    cover, last_covered_activity, next_activity_to_cover)
            cover.pattern_stream.add(
                    next_current_covering_pattern.pattern,
                    cover.get_all_pattern_names())
        return next_current_covering_pattern

    def _skip_intermediate_patterns(
            self, cover: Cover, last_covered_activity,
            preceding_pattern: Pattern, intermediate_patterns: List[Pattern]):
        for intermediate_pattern_activity in intermediate_patterns:
            intermediate_node = self.pattern_dfg.nodes[intermediate_pattern_activity]
            cover.add_skipped_pattern(intermediate_node.pattern,
                                      preceding_pattern,
                                      last_covered_activity)

            preceding_pattern = intermediate_node.pattern

    def _get_shortest_path(self, cover, start_pattern: Pattern,
                           end_pattern: Pattern) -> List[str]:
        shortest_path_cache_key = (start_pattern.get_activity_name(),
                                   end_pattern.get_activity_name())
        if shortest_path_cache_key not in self.cached_shortest_paths:
            self.cached_shortest_paths[shortest_path_cache_key] = \
                self.pattern_dfg.compute_shortest_path(
                        shortest_path_cache_key[0],
                        shortest_path_cache_key[1])
        return self.cached_shortest_paths[shortest_path_cache_key]

    def __add_log_move(self, cover: Cover, current_covering_pattern,
                       last_covered_activity: str, activity: str,
                       caused_by_non_existing_loop: bool = False):
        if current_covering_pattern is not None:
            if current_covering_pattern.completed_covering:
                cover.add_log_move(
                        last_covered_activity, activity,
                        self.pattern_dfg.get_coverable_activities(
                            current_covering_pattern.pattern.get_activity_name()))
            elif not caused_by_non_existing_loop:
                cover.add_log_move(
                        last_covered_activity, activity,
                        current_covering_pattern.get_next_coverable_activities())
            else:
                cover.add_log_move(last_covered_activity, activity,
                                   frozenset())
        else:
            cover.add_log_move(last_covered_activity, activity,
                            self.__activities_in_pattern_dfg)
