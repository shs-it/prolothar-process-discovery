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
from typing import List
from prolothar_common.models.eventlog.trace cimport Trace
from prolothar_process_discovery.discovery.proseqo.pattern.pattern cimport Pattern

cdef class CoveringSequence(CoveringPattern):

    def __init__(self, Pattern sequence, Trace trace, str last_covered_activity):
        super().__init__(sequence, trace, last_covered_activity)
        self.current_subpattern_covering = None

    cpdef process_covering_step(self, Cover cover, str last_activity, str next_activity):
        #make sure that an already covered subpattern does not lead to
        #unnessecary model moves
        if not self.can_cover(next_activity):
            self.__add_log_move(cover, last_activity, next_activity)
            return
        if self.pattern.special_noise_set:
            if next_activity in self.pattern.special_noise_set:
                self.__add_log_move(cover, last_activity, next_activity)
                return
            else:
                cover.meta_stream.add_present_code(self.pattern, last_activity)

        if (not self.started_covering or
            self.current_subpattern_covering.completed_covering):
            self._start_covering_on_next_matching_pattern(
                    cover, last_activity, next_activity)
        elif not self.current_subpattern_covering.pattern.contains_activity(next_activity):
            self.current_subpattern_covering.skip_to_end(cover, self.trace, last_activity)
            self._start_covering_on_next_matching_pattern(
                    cover, last_activity, next_activity)
        else:
            #we have to continue covering for current subpattern
            self.current_subpattern_covering.process_covering_step(
                            cover, last_activity, next_activity)

        self.completed_covering = (
            self.current_subpattern_covering.completed_covering and
            self.pattern.get_subpatterns()[-1] == self.current_subpattern_covering.pattern)

    cdef _start_covering_on_next_matching_pattern(
            self, Cover cover, str last_activity, str next_activity):
        self.started_covering = True

        for subpattern in self.__get_uncovered_subpatterns():
            if subpattern.contains_activity(next_activity):
                self.current_subpattern_covering = subpattern.for_covering(
                        self.trace, last_activity)
                self.current_subpattern_covering.process_covering_step(
                        cover, last_activity, next_activity)
                break
            else:
                subpattern.for_covering(
                        self.trace, last_activity).skip_to_end(
                        cover, self.trace, last_activity)
        if self.current_subpattern_covering is None:
            raise NotImplementedError(
                'at least one subpattern must contain "%s" in sequence "%s"' % (
                            next_activity, self.pattern.get_activity_name()))

    def __get_uncovered_subpatterns(self) -> List[Pattern]:
        subpatterns = self.pattern.get_subpatterns()
        if self.current_subpattern_covering is None:
            return subpatterns
        else:
            subpattern_start_index = subpatterns.index(
                    self.current_subpattern_covering.pattern) + 1
            return subpatterns[subpattern_start_index:]

    def __get_already_covered_subpatterns(self) -> List[Pattern]:
        if self.current_subpattern_covering is None:
            return []
        else:
            subpatterns = self.pattern.get_subpatterns()
            subpattern_end_index = subpatterns.index(
                    self.current_subpattern_covering.pattern)
            if self.current_subpattern_covering.completed_covering:
                subpattern_end_index += 1
            return subpatterns[:subpattern_end_index]

    cpdef int skip_to_end(self, Cover cover, Trace trace, str last_covered_activity):
        cdef int nr_of_model_moves = 0
        if self.current_subpattern_covering is not None:
            nr_of_model_moves = self.current_subpattern_covering.skip_to_end(
                    cover, trace, last_covered_activity)
        for subpattern in self.__get_uncovered_subpatterns():
            nr_of_model_moves += (<CoveringPattern>(<Pattern>subpattern).for_covering(
                    trace, last_covered_activity)).skip_to_end(
                    cover, trace, last_covered_activity)
        self.completed_covering = True
        return nr_of_model_moves

    cdef set _get_next_coverable_activities(self):
        cdef set coverable_activities
        if self.current_subpattern_covering.completed_covering:
            coverable_activities = self.__get_uncovered_subpatterns()[
                    0].start_activities()
        else:
            coverable_activities = \
                self.current_subpattern_covering.get_next_coverable_activities()
        coverable_activities.update(self.pattern.special_noise_set)
        return coverable_activities

    cpdef bint can_cover(self, str activity):
        for subpattern in self.__get_already_covered_subpatterns():
            if subpattern.contains_activity(activity):
                return False
        return True

    def __add_log_move(self, cover, last_activity: str, next_activity: str):
        if next_activity not in self.pattern.special_noise_set:
            cover.add_log_move(last_activity, next_activity,
                               self.get_next_coverable_activities())
        elif next_activity in self.pattern.special_noise_set:
            cover.move_stream.add_synchronous_move(last_activity)
            cover.meta_stream.add_absent_code(self.pattern, last_activity)
            cover.meta_stream.add_routing_code_for_given_activity(
                self.pattern, next_activity,
                frozenset(self.pattern.special_noise_set),
                last_activity
            )


