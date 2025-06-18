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

cdef class CoveringLoop(CoveringPattern):
    """implements covering for the Loop Pattern"""

    def __init__(self, Pattern loop, Trace trace, str last_covered_activity):
        super().__init__(loop, trace, last_covered_activity)
        self.covering_subpattern = None
        self.loop_iterations = 0

    cpdef process_covering_step(self, Cover cover, str last_activity, str next_activity):
        if self.completed_covering:
            raise ValueError('loop already completed')
        if not self.started_covering:
            self.started_covering = True
            if self.pattern.contains_activity(next_activity):
                self.covering_subpattern = (<Pattern>self.pattern.get_subpatterns()[
                        0]).for_covering(self.trace, last_activity)
            else:
                raise ValueError('subpattern must contain activity at start')

        #prepare next loop iteration if necessary
        if not self.covering_subpattern.can_cover(next_activity):
            self.covering_subpattern.skip_to_end(cover, self.trace,
                                                 last_activity)

        #start next loop iteration if necessary
        if self.covering_subpattern.completed_covering:
            self.covering_subpattern = self.covering_subpattern.pattern.for_covering(
                    self.trace, self.last_covered_activity_before_this_pattern)
            cover.meta_stream.add_repeat_code(self.pattern, self.loop_iterations,
                                              last_activity)
            self.loop_iterations += 1
            self.covering_subpattern.process_covering_step(
                    cover, self.last_covered_activity_before_this_pattern,
                    next_activity)
        else:
            self.covering_subpattern.process_covering_step(
                    cover, last_activity, next_activity)

    cpdef int skip_to_end(self, Cover cover, Trace trace, str last_covered_activity):
        cdef int model_moves
        if not self.completed_covering:
            #we have to do at least 1 loop iteration
            if self.covering_subpattern is None:
                self.covering_subpattern = (<Pattern>self.pattern.get_subpatterns()[
                            0]).for_covering(self.trace, last_covered_activity)

            model_moves = self.covering_subpattern.skip_to_end(
                    cover, trace, last_covered_activity)
            cover.meta_stream.add_end_code(self.pattern, self.loop_iterations,
                                           last_covered_activity)
            self.completed_covering = True
            return model_moves
        else:
            return 0

    cdef set _get_next_coverable_activities(self):
        if self.covering_subpattern.completed_covering:
            return self.covering_subpattern.pattern.start_activities()
        else:
            return self.covering_subpattern.get_next_coverable_activities()

    cpdef bint can_cover(self, str activity):
        return self.pattern.contains_activity(activity)
