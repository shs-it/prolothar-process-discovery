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

cdef class PatternStream:
    """pattern stream of cover, i.e. a stream of patterns that is used to
    cover (= encode) a set of sequences"""

    cdef dict _usage_per_pattern_conditional
    cdef bint _store_patterns
    cdef list _pattern_sequence
    cdef dict __pattern_sequence_cache
    cdef list __current_trace_cache
    cdef tuple __current_trace

    cpdef PatternStream copy_counts_only(self)
    cpdef add(
        self, Pattern pattern, frozenset usable_pattern_activities,
        bint add_to_cache = ?, int count = ?)
    cpdef remove(self, Pattern pattern, frozenset usable_pattern_activities, int count = ?)
    cpdef remove_pattern_from_context(self, frozenset context, Pattern pattern)
    cpdef float get_code_length(self, bint verbose=?)
    cpdef start_trace_covering(self, tuple trace)
    cpdef end_trace_covering(self, tuple trace)
    cpdef use_cache_to_cover_trace(self, tuple trace)
