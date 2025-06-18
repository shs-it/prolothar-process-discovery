from prolothar_process_discovery.discovery.proseqo.pattern.pattern cimport Pattern
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_pattern cimport CoveringPattern

cdef class Singleton(Pattern):
    cdef public str activity