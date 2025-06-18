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
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_pattern cimport CoveringPattern
from prolothar_process_discovery.discovery.proseqo.cover cimport Cover

cdef class CoveringInclusiveChoice(CoveringPattern):

    def __init__(self, choice: Pattern, trace, last_covered_activity: str):
        super().__init__(choice, trace, last_covered_activity)
        self.covering_options = [
                option.for_covering(trace, last_covered_activity)
                for option in choice.options]
        self.current_subpattern_covering = None

    cpdef process_covering_step(self, Cover cover, str last_activity, str next_activity):
        cdef CoveringPattern other_covering_option
        if not self.started_covering:
            self.started_covering = True
            self.current_subpattern_covering = \
                self.__find_matching_subpattern(next_activity)
            if self.current_subpattern_covering is not None:
                self.__add_routing_code(cover, last_activity)
            else:
                raise ValueError('No option of %r contains activity %s' % (
                        self.pattern, next_activity))

        if self.completed_covering:
            raise ValueError('unallowed covering: already completed covering')

        if self.current_subpattern_covering.pattern.contains_activity(next_activity):
            if not self.current_subpattern_covering.completed_covering:
                self.current_subpattern_covering.process_covering_step(
                        cover, last_activity, next_activity)
            else:
                cover.add_log_move(last_activity, next_activity,
                                   self.get_next_coverable_activities())
        else:
            other_covering_option = self.__find_matching_subpattern(next_activity)

            if other_covering_option is not None:
                if not self.current_subpattern_covering.completed_covering:
                    self.current_subpattern_covering.skip_to_end(
                            cover, self.trace, last_activity)
                self.covering_options.remove(self.current_subpattern_covering)
                self.current_subpattern_covering = other_covering_option
                self.__add_routing_code(cover, last_activity)
                self.current_subpattern_covering.process_covering_step(
                        cover, last_activity, next_activity)
            else:
                #an already used option must contain the activity
                #=> we have to make a log move
                cover.add_log_move(last_activity, next_activity,
                                   self.get_next_coverable_activities())

        self.completed_covering = len(self.covering_options) == 1 and \
            self.covering_options[0].completed_covering

    cdef CoveringPattern __find_matching_subpattern(self, str next_activity):
        cdef CoveringPattern option
        for option in self.covering_options:
            if option.pattern.contains_activity(next_activity):
                return option

    def __add_routing_code(self, cover, last_activity: str):
       """adds a routing code to the current covering subpattern"""
       cover.meta_stream.add_routing_code(
            self.pattern,
            self.current_subpattern_covering.pattern,
            frozenset(c.pattern.get_activity_name()
                      for c in self.covering_options),
            last_activity)

    cpdef int skip_to_end(self, Cover cover, Trace trace, str last_covered_activity):
        if not self.completed_covering:
            self.completed_covering = True
            if self.current_subpattern_covering is not None:
                return self.current_subpattern_covering.skip_to_end(
                        cover, trace, last_covered_activity)
            else:
                return self.covering_options[0].skip_to_end(
                        cover, trace, last_covered_activity)

    cpdef set get_next_coverable_activities(self):
        cdef set coverable_activities
        cdef CoveringPattern option
        if not self.current_subpattern_covering.completed_covering:
            return self.current_subpattern_covering.get_next_coverable_activities()
        else:
            coverable_activities = set()
            for option in self.covering_options:
                if option != self.current_subpattern_covering:
                    coverable_activities.update(option.get_next_coverable_activities())
            return coverable_activities

    cpdef bint can_cover(self, str activity):
        for option in self.covering_options:
            if option.can_cover(activity):
                return True
        return False
