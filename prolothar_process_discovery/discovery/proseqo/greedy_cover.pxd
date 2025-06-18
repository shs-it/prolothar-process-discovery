from prolothar_process_discovery.discovery.proseqo.pattern.pattern cimport Pattern
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_pattern cimport CoveringPattern
from prolothar_process_discovery.discovery.proseqo.cover cimport Cover
from prolothar_process_discovery.discovery.proseqo.pattern_dfg cimport PatternDfg
from prolothar_common.models.eventlog.trace cimport Trace
from prolothar_common.models.eventlog.event cimport Event

cpdef Cover compute_cover(
        list trace_list, PatternDfg pattern_dfg,
        bint store_patterns_in_pattern_stream=?,
        set activity_set=?)

cdef class GreedyCoverComputer:
    cdef PatternDfg pattern_dfg
    cdef dict cached_shortest_paths
    cdef dict cached_reachable_activities
    cdef dict cached_patterns_for_activity
    cdef set __activities_in_pattern_dfg

    cpdef Cover compute(self, list trace_list,
        bint store_patterns_in_pattern_stream = ?,
        set activity_set = ?,
        Cover cover = ?)

    cdef _extend_cover_for_trace(self, Cover cover, Trace trace)

    #list[str], 2x Pattern
    cdef list _get_shortest_path(self, Pattern start_pattern, Pattern end_pattern)

    cdef CoveringPattern _handle_pattern_change_in_cover(
            self, CoveringPattern current_covering_pattern, Cover cover,
            Trace trace, Pattern next_matching_pattern,
            str last_covered_activity,
            str next_activity_to_cover)

    cdef _skip_intermediate_patterns(
            self, Cover cover, str last_covered_activity,
            Pattern preceding_pattern, list intermediate_patterns)

    cdef __add_log_move(self, Cover cover, CoveringPattern current_covering_pattern,
                       str last_covered_activity, str activity,
                       bint caused_by_non_existing_loop)

    cdef dict __create_cached_patterns_for_activities(self)

    cdef list __get_next_matching_patterns(self, Event event)

    cdef CoveringPattern __cover_event_using_pattern(
            self, CoveringPattern current_covering_pattern, 
            Pattern pattern,
            str last_covered_activity, 
            Event event, 
            Cover cover, 
            Trace trace)

    cdef CoveringPattern _handle_continue_pattern_in_cover(
            self, CoveringPattern current_covering_pattern, Cover cover,
            Trace trace, str last_covered_activity,
            str next_activity_to_cover)