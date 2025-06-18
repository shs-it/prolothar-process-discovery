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
"""
contains logic for covering a subtrace with a SubGraph pattern
"""

from prolothar_common.models.eventlog.trace cimport Trace
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_pattern cimport CoveringPattern
from prolothar_process_discovery.discovery.proseqo.cover cimport Cover

from typing import List

cdef class CoveringSubGraph(CoveringPattern):

    def __init__(self, object community, object trace, str last_covered_activity):
        super().__init__(community, trace, last_covered_activity)
        self.current_node = None
        self.covering_subpattern = None

    cpdef process_covering_step(self, Cover cover, str last_activity, str next_activity):
        if self.completed_covering:
            raise ValueError('covering already completed')
        if not self.started_covering:
            self._start_covering(cover, last_activity, next_activity)
        else:
            self._continue_covering(cover, last_activity, next_activity)

    cdef _start_covering(self, Cover cover, str last_activity, str next_activity):
        self.current_node = self.pattern.find_node_containing_activity(next_activity)
        if self.current_node is None:
            self.__add_log_move(cover, last_activity, next_activity)
        else:
            shortest_path = self._get_shortest_path_from_sources()
            if shortest_path:
                self._skip_activities(cover, None, shortest_path[1:-1],
                                      last_activity)
                self._start_covering_current_node(
                        cover, last_activity, next_activity,
                        self.pattern.pattern_dfg.get_following_activities(
                                shortest_path[-2]))
            else:
                self._start_covering_current_node(
                        cover,last_activity,  next_activity,
                        self.pattern.get_start_activities())
            self.started_covering = True

    def _continue_covering(self, cover, last_activity: str, next_activity: str):
        next_node = self.pattern.find_node_containing_activity(next_activity)
        if next_node is None:
            self.__add_log_move(cover, last_activity, next_activity)
        elif self.current_node == next_node:
            if not self.covering_subpattern.completed_covering:
                self.covering_subpattern.process_covering_step(
                        cover, last_activity, next_activity)
            #elif is selfloop
            elif self.current_node.is_followed_by(next_activity):
                self._start_covering_current_node(
                        cover, last_activity, next_activity,
                        self.pattern.pattern_dfg.get_following_activities(
                            next_node.activity))
            else:
                self.__add_log_move(cover, last_activity, next_activity)
        else:
            self.covering_subpattern.skip_to_end(cover, self.trace, last_activity)
            shortest_path = self._get_shortest_path(
                self.current_node.activity, next_node.activity)
            if shortest_path:
                self._skip_activities(cover, shortest_path[0],
                                      shortest_path[1:-1], last_activity)
                self.current_node = next_node
                self._start_covering_current_node(
                        cover, last_activity, next_activity,
                        self.pattern.pattern_dfg.get_following_activities(
                                shortest_path[-2]))
            else:
                self.__add_log_move(cover, last_activity, next_activity)

    def _start_covering_current_node(
            self, cover, str last_activity, next_activity: str,
            alternatives: List[str]):
        try:
            cover.meta_stream.add_routing_code(
                    self.pattern, self.current_node.pattern,
                    frozenset(alternatives), last_activity)
        except KeyError as e:
            print('###################')
            self.pattern.pattern_dfg.plot()
            print(self.current_node.pattern)
            print(self.current_node)
            print(alternatives)
            print('###################')
            raise e
        self.covering_subpattern = self.current_node.pattern.for_covering(
                self.trace, last_activity)
        self.covering_subpattern.process_covering_step(
                cover, last_activity, next_activity)

    cdef _skip_activities(self, Cover cover, str preceding_activity,
                         list skip_activities, str last_activity):
        self._skip_preceding_activity = preceding_activity
        for activity in skip_activities:
            pattern = self.pattern.pattern_dfg.nodes[activity].pattern
            if self._skip_preceding_activity:
                alternatives = set(
                        self.pattern.pattern_dfg.get_following_activities(
                                self._skip_preceding_activity))
            else:
                alternatives = set(self.pattern.get_start_activities())
            alternatives.add(pattern.get_activity_name())
            cover.meta_stream.add_routing_code(
                    self.pattern, pattern,
                    frozenset(alternatives), last_activity)
            pattern.for_covering(
                    self.trace, last_activity).skip_to_end(
                    cover, self.trace, last_activity)
            self._skip_preceding_activity = activity
        self._skip_preceding_activity = None

    def _get_shortest_path_from_sources(self):
        shortest_shortest_path = None
        len_of_shortest_shortest_path = float('inf')
        for start_activity in self.pattern.get_start_activities():
            shortest_path = self._get_shortest_path(
                    start_activity, self.current_node.activity)
            if shortest_path and len(shortest_path) < len_of_shortest_shortest_path:
                shortest_shortest_path = shortest_path
                len_of_shortest_shortest_path = len(shortest_path)
        return shortest_shortest_path

    def _get_shortest_path_from_sources_to_sinks(self):
        shortest_shortest_path = None
        len_of_shortest_shortest_path = float('inf')
        for start_activity in self.pattern.get_start_activities():
            for end_activity in self.pattern.get_end_activities():
                shortest_path = self._get_shortest_path(start_activity,
                                                        end_activity)
                if shortest_path and len(shortest_path) < len_of_shortest_shortest_path:
                    shortest_shortest_path = shortest_path
                    len_of_shortest_shortest_path = len(shortest_path)
        return shortest_shortest_path

    cpdef int skip_to_end(self, Cover cover, Trace trace, str last_covered_activity):
        cdef int number_of_skipped_activities = 0
        if self.covering_subpattern is not None:
            self.covering_subpattern.skip_to_end(
                    cover, trace, last_covered_activity)

            if len(self.current_node.edges) > 0:
                shortest_path_to_sink = self._get_shortest_path_to_sinks()
                if shortest_path_to_sink is not None:
                    number_of_skipped_activities = len(shortest_path_to_sink) - 1
                    self._skip_activities(
                            cover, shortest_path_to_sink[0],
                            shortest_path_to_sink[1:],
                            last_covered_activity)
                else:
                    #TODO: this can only happen in rare cases. how to deal with it?
                    pass
        else:
            shortest_path_to_sink = self._get_shortest_path_from_sources_to_sinks()
            if shortest_path_to_sink is None:
                cover.meta_stream.add_routing_code(
                    self.pattern, self.pattern.get_subpatterns()[0].get_activity_name(),
                    self.__get_set_of_subpattern_names(),
                    last_covered_activity)
                self.pattern.get_subpatterns()[0].for_covering(
                        self.trace, last_covered_activity).skip_to_end(
                                cover, self.trace, last_covered_activity)
            else:
                number_of_skipped_activities = len(shortest_path_to_sink)
                self._skip_activities(cover, None, shortest_path_to_sink,
                                      last_covered_activity)

        self.completed_covering = True
        return number_of_skipped_activities

    cdef frozenset __get_set_of_subpattern_names(self):
        return frozenset(p.get_activity_name() for p in self.pattern.get_subpatterns())

    def _get_shortest_path_to_sinks(self):
        shortest_shortest_path = None
        len_of_shortest_shortest_path = float('inf')
        for end_activity in self.pattern.get_end_activities():
            shortest_path = self._get_shortest_path(
                    self.current_node.activity, end_activity)
            if shortest_path and len(shortest_path) < len_of_shortest_shortest_path:
                shortest_shortest_path = shortest_path
                len_of_shortest_shortest_path = len(shortest_path)
        return shortest_shortest_path

    def _get_shortest_path(self, start: str, end: str):
        return self.pattern.compute_shortest_path(start, end)

    cdef set _get_next_coverable_activities(self):
        if self.covering_subpattern.completed_covering:
            coverable_activities = set()
            for edge in self.current_node.edges:
                coverable_activities.update(edge.end.pattern.start_activities())
            return coverable_activities
        else:
            return self.covering_subpattern.get_next_coverable_activities()

    def __add_log_move(self, cover, last_activity: str, activity: str):
        cover.add_log_move(last_activity, activity,
                           self.get_next_coverable_activities())

    cpdef bint can_cover(self, str activity):
        if self.current_node is None:
            return self.pattern.contains_activity(activity)
        elif self.covering_subpattern.can_cover(activity):
            return True
        else:
            next_node = \
                self.pattern.find_node_containing_activity(activity)
            return self._get_shortest_path(
                self.current_node.activity, next_node.activity)


