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

from typing import List, Set

from prolothar_process_discovery.discovery.proseqo.pattern_dfg cimport PatternDfg
from prolothar_common.models.eventlog import EventLog
from prolothar_common.models.dfg.node cimport Node

cpdef Cover compute_cover(
    list trace_list, PatternDfg pattern_dfg,
    bint store_patterns_in_pattern_stream=False,
    set activity_set=None):
    """computes a Cover for a PatternDfg on a given list of Traces. This
    method is a convenience method that uses an instance of
    GreedyCoverComputer"""
    return GreedyCoverComputer(pattern_dfg).compute(
            trace_list,
            store_patterns_in_pattern_stream=store_patterns_in_pattern_stream,
            activity_set=activity_set)

cdef class GreedyCoverComputer:
    """computes a Cover for a PatternDfg on a given list of Traces"""
    def __init__(self, pattern_dfg: PatternDfg):
        self.pattern_dfg = pattern_dfg
        self.cached_shortest_paths = {}
        self.cached_reachable_activities = {}
        self.cached_patterns_for_activity = \
            self.__create_cached_patterns_for_activities()
        self.__activities_in_pattern_dfg = set()
        cdef Node node
        for node in pattern_dfg.nodes.values():
            self.__activities_in_pattern_dfg.update(
                    (<Pattern>node.pattern).get_activity_set())

    cdef dict __create_cached_patterns_for_activities(self):
        """returns a dictionary that stores for each activity in which
        patterns (activity names of the these patterns) this activity occurs.

        returns Dict[str, List[str]]
        """
        cdef dict cached_patterns_for_activity = {}
        cdef Node node
        for node in self.pattern_dfg.nodes.values():
            for activity in (<Pattern>node.pattern).get_activity_set():
                try:
                    (<list>cached_patterns_for_activity[activity]).append(node.pattern)
                except KeyError:
                    cached_patterns_for_activity[activity] = [node.pattern]
        return cached_patterns_for_activity

    cpdef Cover compute(self, list trace_list,
                bint store_patterns_in_pattern_stream = False,
                set activity_set = None,
                Cover cover = None):
        """computes a Cover for a PatternDfg on a given list of Traces"""

        if activity_set is None:
            event_log = EventLog()
            event_log.traces = trace_list
            activity_set = event_log.compute_activity_set()

        if cover is None:
            cover = Cover(
                self.pattern_dfg, activity_set,
                store_patterns_in_pattern_stream=store_patterns_in_pattern_stream)

        cdef Trace trace
        for trace in trace_list:
            if cover.can_cover_trace_with_cache(trace):
                cover.use_cache_to_cover_trace(trace)
            else:
                self._extend_cover_for_trace(cover, trace)

        return cover

    cdef _extend_cover_for_trace(self, Cover cover, Trace trace):
        cover.start_trace_covering(trace)
        cdef CoveringPattern current_covering_pattern = None
        cdef str last_covered_activity = None
        cdef Event event
        cdef list next_matching_patterns
        for event in trace.events:
            next_matching_patterns = self.__get_next_matching_patterns(event)
            #if there is no pattern containing the activity, we have a log move
            if not next_matching_patterns:
                self.__add_log_move(
                        cover, current_covering_pattern,
                        last_covered_activity, 
                        <str>event.activity_name,
                        False)
            #currently, we expect that only one high-level pattern contains the activity
            elif len(next_matching_patterns) > 1:
                raise NotImplementedError(
                        'more than one matching pattern for "%s"' % event.activity_name)
            #standard case: there is exactly one pattern containing the activity
            else:
                current_covering_pattern = self.__cover_event_using_pattern(
                        current_covering_pattern, next_matching_patterns[0],
                        last_covered_activity, event, cover, trace)
            last_covered_activity = <str>event.activity_name
        cover.end_trace_covering(trace)

    cdef list __get_next_matching_patterns(self, Event event):
        try:
            return <list>(self.cached_patterns_for_activity[event.activity_name])
        except KeyError:
            #Pattern DFG does not contain activity
            return []

    cdef CoveringPattern __cover_event_using_pattern(
            self, CoveringPattern current_covering_pattern, 
            Pattern pattern,
            str last_covered_activity, 
            Event event, 
            Cover cover, 
            Trace trace):
        #case 1: we are still in the same pattern and continue our cover with
        #this pattern
        if (current_covering_pattern is not None and
            pattern == current_covering_pattern.pattern):
            current_covering_pattern = self._handle_continue_pattern_in_cover(
                    current_covering_pattern, cover, trace,
                    last_covered_activity, 
                   <str>event.activity_name)
        #case 2: we have a pattern change
        else:
            current_covering_pattern = self._handle_pattern_change_in_cover(
                    current_covering_pattern, cover, trace,
                    pattern, last_covered_activity,
                    <str>event.activity_name)

        return current_covering_pattern

    cdef CoveringPattern _handle_continue_pattern_in_cover(
            self, CoveringPattern current_covering_pattern, Cover cover,
            Trace trace, str last_covered_activity,
            str next_activity_to_cover):
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
                                    True)
        else:
            current_covering_pattern.process_covering_step(
                    cover, last_covered_activity, next_activity_to_cover)
        return current_covering_pattern

    cdef CoveringPattern _handle_pattern_change_in_cover(
            self, CoveringPattern current_covering_pattern, Cover cover,
            Trace trace, Pattern next_matching_pattern,
            str last_covered_activity,
            str next_activity_to_cover):
        """
            1. first we have to finish covering with current pattern by using skip events
            2. if we have intermediate patterns between the two patterns in the
               pattern dfg, then we have to skip them (model moves)
            3. then we can start to use the next pattern
            Exception: there is no path between the two patterns => log move
        """
        if current_covering_pattern is not None:
            shortest_path = self._get_shortest_path(
                    current_covering_pattern.pattern,
                    next_matching_pattern)
            if shortest_path:
                current_covering_pattern.skip_to_end(
                    cover, trace, last_covered_activity)

                self._skip_intermediate_patterns(
                    cover, 
                    last_covered_activity,
                    current_covering_pattern.pattern, 
                    shortest_path[1:-1]
                )
                next_current_covering_pattern = next_matching_pattern.for_covering(
                        trace, last_covered_activity)
                cover.pattern_stream.add(
                        next_current_covering_pattern.pattern,
                        cover.get_following_activities(<str>shortest_path[-2]))
                next_current_covering_pattern.process_covering_step(
                        cover, last_covered_activity, next_activity_to_cover)
            else:
                self.__add_log_move(cover, current_covering_pattern,
                                    last_covered_activity, next_activity_to_cover, 
                                    False)
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

    cdef _skip_intermediate_patterns(
            self, Cover cover, str last_covered_activity,
            Pattern preceding_pattern, list intermediate_patterns):
        for intermediate_pattern_activity in intermediate_patterns:
            intermediate_node = self.pattern_dfg.nodes[intermediate_pattern_activity]
            cover.add_skipped_pattern(
                <Pattern>((<Node>intermediate_node).pattern),
                preceding_pattern,
                last_covered_activity
            )
            preceding_pattern = <Pattern>((<Node>intermediate_node).pattern)

    cdef list _get_shortest_path(self, Pattern start_pattern, Pattern end_pattern):
        shortest_path_cache_key = (
            start_pattern.get_activity_name(),
            end_pattern.get_activity_name()
        )
        cdef list shortest_path = <list>(self.cached_shortest_paths.get(shortest_path_cache_key, None))
        if shortest_path is None:
            shortest_path = self.pattern_dfg.compute_shortest_path(
                start_pattern.get_activity_name(), end_pattern.get_activity_name()
            )
            self.cached_shortest_paths[shortest_path_cache_key] = shortest_path
        return shortest_path

    cdef __add_log_move(self, Cover cover, CoveringPattern current_covering_pattern,
                       str last_covered_activity, str activity,
                       bint caused_by_non_existing_loop):
        if current_covering_pattern is not None:
            if current_covering_pattern.completed_covering:
                cover.add_log_move(
                    last_covered_activity, activity,
                    self.pattern_dfg.get_coverable_activities(
                        current_covering_pattern.pattern.get_activity_name())
                )
            elif not caused_by_non_existing_loop:
                cover.add_log_move(
                    last_covered_activity, activity,
                    current_covering_pattern.get_next_coverable_activities()
                )
            else:
                cover.add_log_move(last_covered_activity, activity, set())
        else:
            cover.add_log_move(last_covered_activity, activity, self.__activities_in_pattern_dfg)
