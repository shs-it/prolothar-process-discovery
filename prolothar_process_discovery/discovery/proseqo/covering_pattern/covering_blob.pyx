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

from prolothar_common.models.eventlog.trace cimport Trace
from prolothar_process_discovery.discovery.proseqo.pattern.pattern cimport Pattern
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_pattern cimport CoveringPattern
from prolothar_process_discovery.discovery.proseqo.cover cimport Cover

cdef class CoveringBlob(CoveringPattern):
    """implements covering for the Blob Pattern"""

    def __init__(self, Pattern blob, Trace trace, str last_covered_activity):
        super().__init__(blob, trace, last_covered_activity)
        self.__iterations = 1

    cpdef process_covering_step(self, Cover cover, str last_activity, str next_activity):
        if not self.pattern.contains_activity(next_activity):
            raise ValueError('subpattern must contain activity at start')

        if self.started_covering:
            cover.meta_stream.add_repeat_code(self.pattern, self.__iterations,
                                              last_activity)
            self.__iterations += 1
        else:
            self.started_covering = True

        if last_activity != next_activity:
            cover.move_stream.add_synchronous_move(last_activity)
            cover.meta_stream.add_routing_code_for_given_activity(
                self.pattern, next_activity,
                frozenset(self.pattern.get_activity_set().difference([last_activity])),
                last_activity)
        else:
            cover.add_log_move(
                last_activity, next_activity,
                self.get_next_coverable_activities().difference([last_activity]))


    cpdef int skip_to_end(self, Cover cover, Trace trace, str last_covered_activity):
        #we can end in a blob at any time, but we have to take it at least once
        cdef int model_moves = 0
        if not self.started_covering:
            model_moves = 1
            cover.move_stream.add_model_move(last_covered_activity)
            default_activity = list(sorted(self.pattern.get_activity_set()))[0]
            cover.meta_stream.add_routing_code_for_given_activity(
                self.pattern, 
                <str>default_activity,
                frozenset(self.pattern.get_activity_set()),
                last_covered_activity)
        cover.meta_stream.add_end_code(self.pattern, self.__iterations,
                                       last_covered_activity)
        self.completed_covering = True
        return model_moves

    cdef set _get_next_coverable_activities(self):
        return self.pattern.get_activity_set()

    cpdef bint can_cover(self, str activity):
        return self.pattern.contains_activity(activity)