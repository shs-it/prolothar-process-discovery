from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_pattern cimport CoveringPattern
from prolothar_common.models.directly_follows_graph cimport DirectlyFollowsGraph

cdef class Pattern:
    cdef str __cached_activity_name
    cdef set __cached_start_activities
    cdef set __cached_end_activities
    cdef int __cached_hash
    cdef set __cached_activity_set

    cpdef str get_activity_name(self)
    cpdef set get_activity_set(self)
    cpdef list get_subpatterns(self)
    cpdef list get_start_subpatterns(self)
    cpdef list get_end_subpatterns(self)
    cpdef Pattern copy(self)
    cpdef Pattern _copy(self)
    cpdef CoveringPattern for_covering(self, trace, str last_covered_activity)
    cpdef tuple get_encoded_length_in_code_table(self, frozenset available_activities)
    cpdef bint contains_activity(self, str activity)
    cpdef bint is_singleton(self)
    cpdef set start_activities(self)
    cpdef fold_dfg(self, DirectlyFollowsGraph dfg)