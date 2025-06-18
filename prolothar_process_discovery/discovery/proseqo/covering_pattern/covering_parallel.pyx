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
from prolothar_process_discovery.discovery.proseqo.cover cimport Cover
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_pattern cimport CoveringPattern

cdef class CoveringParallel(CoveringPattern):

    def __init__(self, Pattern parallel, Trace trace, last_covered_activity: str):
        super().__init__(parallel, trace, last_covered_activity)
        self.covering_branches = [
                (<Pattern>branch).for_covering(trace, last_covered_activity)
                for branch in parallel.branches]
        self.nr_of_completed_branches = 0

    cpdef process_covering_step(self, Cover cover, str last_activity, str next_activity):
        self.started_covering = True

        cdef bint success = False
        cdef list uncovered_branches = self.__get_uncovered_branches()
        cdef CoveringPattern branch
        for branch in uncovered_branches:
            if branch.pattern.contains_activity(next_activity):
                cover.meta_stream.add_routing_code(
                        self.pattern, branch.pattern,
                        self.__get_pattern_names_of_branches(uncovered_branches),
                        last_activity)
                branch.process_covering_step(cover, last_activity, next_activity)
                success = True
                if branch.completed_covering:
                    self.nr_of_completed_branches += 1
                break

        if not success:
            #No branch that is not already completed found => log move
            cover.add_log_move(last_activity, next_activity,
                               self.get_next_coverable_activities())

        self.completed_covering = self.nr_of_completed_branches == self.pattern.get_nr_of_subpatterns()

    cpdef int skip_to_end(self, Cover cover, Trace trace, str last_covered_activity):
        cdef int nr_of_model_moves_in_total = 0
        cdef list uncovered_branches = self.__get_uncovered_branches()
        cdef CoveringPattern branch
        while uncovered_branches:
            branch = uncovered_branches.pop()
            nr_of_model_moves = branch.skip_to_end(cover, trace, last_covered_activity)
            available_pattern_names = self.__get_pattern_names_of_branches(uncovered_branches + [branch])
            for _ in range(nr_of_model_moves):
                cover.meta_stream.add_routing_code(
                        self.pattern, branch.pattern,
                        available_pattern_names,
                        last_covered_activity)
            nr_of_model_moves_in_total += nr_of_model_moves
        return nr_of_model_moves_in_total

    cdef list __get_uncovered_branches(self):
        return [
            branch for branch in self.covering_branches
            if not (<CoveringPattern>branch).completed_covering
        ]

    cdef frozenset __get_pattern_names_of_branches(self, list branches):
        return frozenset(b.pattern.get_activity_name() for b in branches)

    cdef set _get_next_coverable_activities(self):
        cdef set next_coverable_activities = set()
        cdef CoveringPattern branch
        for branch in self.covering_branches:
            if not branch.completed_covering:
                next_coverable_activities.update(branch.get_next_coverable_activities())
        return next_coverable_activities

    cpdef bint can_cover(self, str activity):
        for branch in self.covering_branches:
            if branch.can_cover(activity):
                return True
        return False
