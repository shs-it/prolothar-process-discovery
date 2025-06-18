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
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_pattern cimport CoveringPattern
from prolothar_process_discovery.discovery.proseqo.cover cimport Cover

cdef class CoveringSubGraph(CoveringPattern):

    cdef object current_node
    cdef CoveringPattern covering_subpattern
    cdef str _skip_preceding_activity

    cdef _start_covering(self, Cover cover, str last_activity, str next_activity)
    cdef frozenset __get_set_of_subpattern_names(self)
    cdef _skip_activities(self, Cover cover, str preceding_activity,
                         list skip_activities, str last_activity)