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

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.dfg.node import Node

from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Place

from typing import Set, List, Tuple

from random import Random

class Pattern:

    def __init__(self): ...

    def expand_dfg(self, node: Node, dfg: DirectlyFollowsGraph, recursive: bool = True): ...

    def fold_dfg(self, dfg: DirectlyFollowsGraph):
        """creates a new node in the dfg and replaces all activities in the dfg
        matching this pattern by this new node
        """
        ...

    def get_start_subpatterns(self) -> List['Pattern']: ...

    def get_end_subpatterns(self) -> List['Pattern']: ...

    def contains_activity(self, activity: str) -> bool:
        """returns True if this pattern or one of its subpatterns contain
        the given activity"""
        ...

    def get_activity_name(self) -> str:
        """returns a readable string representation of this pattern"""
        ...

    def get_activity_set(self) -> Set[str]: ...

    def get_nr_of_subpatterns(self) -> int: ...

    def get_subpatterns(self) -> List['Pattern']: ...

    def for_covering(self, trace, last_covered_activity: str):
        """
        Args:
            trace:
                the trace we want to cover with this pattern
            last_covered_activity:
                the last activity that has been covered before we use this
                pattern. this is used to prevent choices
                from learning which option to pick in which iteration
        """
        ...

    def get_nr_of_forbidden_edges_in_pattern_dfg(self, pattern_dfg) -> int:
        """some patterns make edges in their pattern-directly-follows-graph
        obsolute. for example, a loop pattern A+ implies that there is no edge
        from "A+" to "A+"
        """
        ...

    def get_encoded_length_in_code_table(
            self, available_activities: Set[str]) -> Tuple[float,Set[str]]:
        """computes the MDL of this pattern in the code table.

        Args:
            available_activities:
                the set of available activities to encode this pattern and
                patterns that are encoded after this one. this set determines
                the encoded length of one one activity in this pattern.
        Returns:
            a 2-tuple. the first element is the MDL, the second one is the
            set of available activities for other patterns. this will be
            reduced by the used activities in this pattern if "reuse_activities"
            is False. otherwise it will be the same as given as parameter.
        """
        ...

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str): ...

    def create_node_for_nested_graph(self, node_id: str,
                                     parent_id: str = None) -> NestedGraph.Node: ...

    def without_degeneration(self) -> Tuple['Pattern', bool]:
        """removes unnessescary complex hierarchies of patterns. the definition
        of degeneration is given by the concrete pattern type. for example,
        a list with only one element is degenerated and is replaced by its
        subpattern. invalidates the cache for get_activity_name()
        """
        ...

    def remove_activity(self, activity: str) -> bool:
        """removes an activity (singleton) in this pattern and in its subpatterns.
        Returns True iff the activity was part of this pattern and has been
        removed.
        """
        ...

    def merge_subpatterns(self) -> bool:
        """merges redundant subpattern into this pattern, e.g. if a sequence
        contains subsequences, the subsequence elements are added to the sequence
        and the subsequence is removed"""
        ...

    def copy(self) -> 'Pattern':
        """returns a copy of this pattern"""
        ...

    def clear_cache(self, recursive: bool = False):
        ...

    def is_singleton(self) -> bool: ...

    def is_optional(self) -> bool: ...

    def add_to_petri_net(self, petri_net: DataPetriNet) -> Tuple[Place,Place]:
        """adds places and transitions to this petri net to rebuild this pattern.
        returns start place and end place created by this pattern"""
        ...

    def replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        """recursively replaces all occurences of the given singleton activity
        by a pattern. This method does not throw an Exception of the singleton
        does not occur in this pattern or its subpatterns. The returned pattern
        of this method is not a copy. non-singletons return themselves,
        singletons either return themselves or the given replacement pattern.
        """
        ...

    def replace_direct_subpattern(self, subpattern: 'Pattern',
                                  replacement: 'Pattern'):
        """replaces the given subpattern with the given replacement. the
        subpattern must be a direct child of this pattern, otherwise an error
        will be thrown
        """
        ...

    def start_activities(self) -> Set[str]:
        """returns a set of activities that must be visited first
        during a complete cover of the pattern. for performance reasons,
        this method caches its result, i.e. a pattern should not have been
        changed during two successive calls of this method. public methods of
        the pattern class that change the internal structure
        (e.g. replace_singleton()) reset the cache and are thus safe to use.
        """
        ...

    def end_activities(self) -> Set[str]:
        """returns a set of activities that must be visited eventually
        during a complete cover of the pattern. for performance reasons,
        this method caches its result, i.e. a pattern should not have been
        changed during two successive calls of this method. public methods of
        the pattern class that change the internal structure
        (e.g. replace_singleton()) reset the cache and are thus safe to use.
        """
        ...

    def generate_activities(self, random: Random = None) -> List[str]:
        """method for log generation"""
        ...
