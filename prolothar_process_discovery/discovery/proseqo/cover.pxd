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

from prolothar_common.models.eventlog import EventLog
from prolothar_common.models.eventlog.trace cimport Trace

from prolothar_process_discovery.discovery.proseqo.pattern_dfg cimport PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.pattern cimport Pattern
from prolothar_process_discovery.discovery.proseqo.cover_streams.pattern_stream cimport PatternStream
from prolothar_process_discovery.discovery.proseqo.cover_streams.meta_stream cimport MetaStream
from prolothar_process_discovery.discovery.proseqo.cover_streams.move_stream cimport MoveStream

cdef class Cover:
    cdef public PatternStream pattern_stream
    cdef public MetaStream meta_stream
    cdef public MoveStream move_stream
    cdef public PatternDfg pattern_dfg
    cdef public frozenset activity_set
    cdef Trace __current_trace
    cdef set __covered_activity_lists
    cdef dict __following_activities_cache
    cdef frozenset __all_pdfg_activity_names

    cpdef Cover copy_counts_only(self)

    cpdef float get_encoded_length_of_cover(self, log: EventLog, bint verbose=?)

    cpdef add_log_move(self, str last_covered_activity, str activity_to_cover,
                       set model_available_activities)

    cpdef add_skipped_pattern(self, Pattern pattern, Pattern preceding_pattern, str last_covered_activity)

    cpdef frozenset get_all_pattern_names(self)

    cpdef frozenset get_following_activities(self, str activity)

    cpdef start_trace_covering(self, Trace trace)

    cpdef end_trace_covering(self, Trace trace)

    cpdef bint can_cover_trace_with_cache(self, Trace trace)

    cpdef use_cache_to_cover_trace(self, Trace trace)

    cpdef frozenset get_activity_set(self)

    cpdef PatternDfg get_pattern_dfg_with_restored_counts(self)