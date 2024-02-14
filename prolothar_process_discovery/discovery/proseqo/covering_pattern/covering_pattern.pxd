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

    cdef public object pattern
    cdef public bint started_covering
    cdef public bint completed_covering
    cdef public object trace
    cdef public object last_covered_activity_before_this_pattern

    cpdef process_covering_step(self, object cover, str last_activity, str next_activity)
    cpdef int skip_to_end(self, object cover, object trace, str last_covered_activity)
    cpdef set get_next_coverable_activities(self)
    cdef set _get_next_coverable_activities(self)
    cpdef bint can_cover(self, str activity)