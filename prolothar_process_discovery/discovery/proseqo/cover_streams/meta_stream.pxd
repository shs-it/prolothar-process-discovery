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
from prolothar_process_discovery.discovery.proseqo.pattern.pattern cimport Pattern

cdef class MetaStream:
    cdef dict __pattern_meta_code_conditional_counter
    cdef dict __trace_metacodes_cache
    cdef tuple __current_trace
    cdef str __present_code
    cdef str __absent_code
    cdef frozenset __present_absent_codes

    cpdef MetaStream copy_counts_only(self)

    cdef __add_metacode(self, Pattern pattern, str metacode,
                       frozenset possible_metacodes,
                       str last_covered_activity,
                       bint add_to_cache = ?)

    cpdef add_present_code(self, Pattern pattern, str last_covered_activity)

    cpdef add_absent_code(self, Pattern pattern, str last_covered_activity)

    cpdef add_repeat_code(self, Pattern pattern, int iteration, str last_covered_activity)

    cpdef add_end_code(self, Pattern pattern, int iteration, str last_covered_activity)

    cpdef add_routing_code(
        self, Pattern pattern, 
        Pattern subpattern,
        frozenset subpattern_alternatives,
        str last_covered_activity)

    cpdef add_routing_code_for_given_activity(
        self, Pattern pattern, 
        str next_activity,
        frozenset activity_alternatives,
        str last_covered_activity)

    cpdef float get_code_length(self, bint verbose=?)

    cpdef int get_code_count(self, Pattern pattern, str metacode)

    cpdef dict get_pattern_metacode_counter(self)

    cpdef start_trace_covering(self, tuple trace)

    cpdef end_trace_covering(self, tuple trace)

    cpdef use_cache_to_cover_trace(self, tuple trace)