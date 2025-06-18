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

cdef class CoveringOptional(CoveringPattern):

    def __init__(self, Pattern optional, Trace trace, str last_covered_activity):
        super().__init__(optional, trace, last_covered_activity)
        self.current_subpattern_covering = None

    cpdef process_covering_step(self, Cover cover, str last_activity, str next_activity):
        if self.completed_covering:
            raise ValueError('covering already completed')
        if not self.started_covering:
            self.started_covering = True
            if self.pattern.contains_activity(next_activity):
                cover.meta_stream.add_present_code(self.pattern, last_activity)
                self.current_subpattern_covering = (<Pattern>self.pattern.get_subpatterns(
                        )[0]).for_covering(self.trace, last_activity)
            else:
                raise ValueError('optional pattern must contain activity at start')

        self.current_subpattern_covering.process_covering_step(
                cover, last_activity, next_activity)
        self.completed_covering = self.current_subpattern_covering.completed_covering

    cpdef int skip_to_end(self, Cover cover, Trace trace, str last_covered_activity):
        self.completed_covering = True
        if self.current_subpattern_covering is not None:
            return self.current_subpattern_covering.skip_to_end(
                    cover, trace, last_covered_activity)
        else:
            cover.meta_stream.add_absent_code(self.pattern, last_covered_activity)
            return 1

    cdef set _get_next_coverable_activities(self):
        return self.current_subpattern_covering.get_next_coverable_activities()

    cpdef bint can_cover(self, str activity):
        if self.current_subpattern_covering is not None:
            return self.current_subpattern_covering.can_cover(activity)
        else:
            return self.pattern.contains_activity(activity)
