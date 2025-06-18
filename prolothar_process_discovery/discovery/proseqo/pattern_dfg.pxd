from prolothar_common.models.directly_follows_graph cimport DirectlyFollowsGraph
from prolothar_common.models.dfg.node cimport Node
from prolothar_process_discovery.discovery.proseqo.pattern.pattern cimport Pattern

cdef class PatternDfg(DirectlyFollowsGraph):

    cpdef add_node(self, str activity)
    cpdef PatternDfg copy(self)
    cpdef add_pattern(self, str activity, Pattern pattern)
    cpdef set get_coverable_activities(self, str activity)
    cpdef set compute_activity_set(self)
    cpdef list get_patterns_with_activity(self, str activity)
    cpdef Node find_node_containing_activity(self, str activity)
    cpdef remove_degenerated_patterns(self)