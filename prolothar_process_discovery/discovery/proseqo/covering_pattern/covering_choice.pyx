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

cdef class CoveringChoice(CoveringPattern):

    def __init__(self, Pattern choice, Trace trace, str last_covered_activity):
        super().__init__(choice, trace, last_covered_activity)
        self.current_subpattern_covering = None

    cpdef process_covering_step(self, Cover cover, str last_activity, str next_activity):
        cdef frozenset set_of_subpattern_names
        if not self.started_covering:
            self.started_covering = True
            set_of_subpattern_names = self.__get_set_of_subpattern_names()
            for option in self.pattern.options:
                if (<Pattern>option).contains_activity(next_activity):
                    self.current_subpattern_covering = (<Pattern>option).for_covering(
                            self.trace, last_activity)
                    cover.meta_stream.add_routing_code(
                            self.pattern, (<Pattern>option),
                            set_of_subpattern_names,
                            last_activity)
                    break
            if self.current_subpattern_covering is None:
                raise ValueError('No option of %r contains activity %s' % (
                        self.pattern, next_activity))

        if self.completed_covering:
            raise ValueError('unallowed covering: already completed covering')

        if self.current_subpattern_covering.pattern.contains_activity(next_activity):
            self.current_subpattern_covering.process_covering_step(
                    cover, last_activity, next_activity)
        else:
            #another option contains the activity, but this option not containing
            #activity has already been used for covering and must be finished
            #=> we have to make a log move
            cover.add_log_move(last_activity, next_activity,
                               self.get_next_coverable_activities())

        self.completed_covering = self.current_subpattern_covering.completed_covering

    cdef frozenset __get_set_of_subpattern_names(self):
        return frozenset(
            subpattern.get_activity_name()
            for subpattern in self.pattern.get_subpatterns()
        )

    cpdef int skip_to_end(self, Cover cover, Trace trace, str last_covered_activity):
        self.completed_covering = True
        if self.current_subpattern_covering is not None:
            return self.current_subpattern_covering.skip_to_end(
                    cover, trace, last_covered_activity)
        else:
            return (<Pattern>self.pattern.get_subpatterns()[0]).for_covering(
                    trace, last_covered_activity).skip_to_end(
                            cover, trace, last_covered_activity)

    cdef set _get_next_coverable_activities(self):
        return self.current_subpattern_covering.get_next_coverable_activities()

    cpdef bint can_cover(self, str activity):
        if self.current_subpattern_covering is not None:
            return self.current_subpattern_covering.can_cover(activity)
        else:
            for option in self.pattern.get_subpatterns():
                if option.contains_activity(activity):
                    return True
            return False
