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
cdef class CoveringPattern:

    def __init__(self, Pattern pattern, Trace trace, str last_covered_activity):
        """
        Args:
            pattern:
                the current pattern we use for covering the trace.
                every pattern type has its own subclass of covering pattern
            trace:
                the trace we want to cover
            last_covered_activity:
                the last activity that has been covered before we create this
                covering pattern
        """
        self.pattern = pattern
        self.started_covering = False
        self.completed_covering = False
        self.trace = trace
        self.last_covered_activity_before_this_pattern = last_covered_activity

    cpdef process_covering_step(self, Cover cover, str last_activity, str next_activity):
        raise NotImplementedError(type(self))

    cpdef int skip_to_end(self, Cover cover, Trace trace, str last_covered_activity):
        """skips all activities in this pattern using model moves
        Args:
            cover:
                a Cover object
            trace:
                a Trace. the trace is needed to create covering pattern
                for the intermediately skipped patterns
            last_covered_activity:
                the last activity of the traces that has been covered. this is
                needed to compute conditional probabilities for moves
        Returns:
            The number of model moves that were necessary to skip the pattern
            to the end
        """
        raise NotImplementedError(type(self))

    cpdef set get_next_coverable_activities(self):
        """returns all activities Set[str] that are coverable with one model move"""
        if self.completed_covering:
            raise ValueError('this method must not be called if the pattern '
                             'has completely been used for covering')
        if not self.started_covering:
            return self.pattern.start_activities()
        return self._get_next_coverable_activities()

    cdef set _get_next_coverable_activities(self):
        """returns all activities that are coverable with one model move.
        special cases like the pattern is already covered completely or has not
        been used for covering at all are already handled by the upper class
        """
        raise NotImplementedError(type(self))

    cpdef bint can_cover(self, str activity):
        """returns True iff the status of the covering pattern still allows
        us to cover the given activity in some of the future moves"""
        raise NotImplementedError(type(self))