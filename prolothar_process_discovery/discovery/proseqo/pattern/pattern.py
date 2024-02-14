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

from abc import ABC, abstractmethod
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.directly_follows_graph import Node
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Place

from typing import Set, List, Tuple

from random import Random

class Pattern(ABC):

    def __init__(self):
        self.__cached_activity_name = None
        self.__cached_start_activities = None
        self.__cached_end_activities = None
        self.__cached_hash = None
        self.__cached_activity_set = None

    @abstractmethod
    def expand_dfg(self, node: Node, dfg: DirectlyFollowsGraph,
                   recursive: bool = True):
        pass

    def fold_dfg(self, dfg: DirectlyFollowsGraph):
        """creates a new node in the dfg and replaces all activities in the dfg
        matching this pattern by this new node
        """
        if self.get_activity_name() in dfg.nodes:
            return

        dfg.add_node(self.get_activity_name())

        for subpattern in self.get_subpatterns():
            subpattern.fold_dfg(dfg)

        for subpattern in self.get_start_subpatterns():
            subpattern_node = dfg.nodes[subpattern.get_activity_name()]
            for edge in subpattern_node.ingoing_edges:
                dfg.add_count(edge.start.activity, self.get_activity_name(),
                              count=edge.count)
        for subpattern in self.get_end_subpatterns():
            subpattern_node = dfg.nodes[subpattern.get_activity_name()]
            for edge in subpattern_node.edges:
                dfg.add_count(self.get_activity_name(), edge.end.activity,
                              count=edge.count)

        #handle self-loops
        dfg.remove_edge((self.get_activity_name(), self.get_activity_name()))
        for end_subpattern in self.get_end_subpatterns():
            for start_subpattern in self.get_start_subpatterns():
                count = dfg.get_count(end_subpattern.get_activity_name(),
                                      start_subpattern.get_activity_name())
                if count > 0:
                    dfg.add_count(self.get_activity_name(),
                                  self.get_activity_name(),
                                  count=count)

        dfg.nodes[self.get_activity_name()].pattern = self
        for subpattern in self.get_subpatterns():
            dfg.remove_node(subpattern.get_activity_name())

    @abstractmethod
    def get_start_subpatterns(self) -> List['Pattern']:
        pass

    @abstractmethod
    def get_end_subpatterns(self) -> List['Pattern']:
        pass

    def contains_activity(self, activity: str):
        """returns True if this pattern or one of its subpatterns contain
        the given activity"""
        return activity in self.get_activity_set()

    def get_activity_name(self) -> str:
        """returns a readable string representation of this pattern"""
        if self.__cached_activity_name is None:
            self.__cached_activity_name = self._generate_activity_name()
        return self.__cached_activity_name

    @abstractmethod
    def _generate_activity_name(self) -> str:
        """returns a readable string representation of this pattern. this method
        is called in a cached version by "get_activity_name()"""
        pass

    def get_activity_set(self) -> Set[str]:
        if self.__cached_activity_set is None:
            self.__cached_activity_set = set()
            for subpattern in self.get_subpatterns():
                self.__cached_activity_set.update(subpattern.get_activity_set())
        return self.__cached_activity_set

    @abstractmethod
    def get_nr_of_subpatterns(self) -> int:
        pass

    @abstractmethod
    def get_subpatterns(self) -> List['Pattern']:
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_nr_of_forbidden_edges_in_pattern_dfg(self, pattern_dfg) -> int:
        """some patterns make edges in their pattern-directly-follows-graph
        obsolute. for example, a loop pattern A+ implies that there is no edge
        from "A+" to "A+"
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str):
        pass

    def create_node_for_nested_graph(self, node_id: str,
                                     parent_id: str = None) -> NestedGraph.Node:
        return NestedGraph.Node(node_id, self.get_activity_name(),
                                parent=parent_id, attributes={
                                    'pattern_type': type(self).__name__})

    def without_degeneration(self) -> Tuple['Pattern', bool]:
        """removes unnessescary complex hierarchies of patterns. the definition
        of degeneration is given by the concrete pattern type. for example,
        a list with only one element is degenerated and is replaced by its
        subpattern. invalidates the cache for get_activity_name()
        """
        pattern_without_degeneration, changed = self._without_degeneration()
        if changed:
            self.__cached_activity_name = None
            self.__cached_hash = None
        return pattern_without_degeneration, changed

    @abstractmethod
    def _without_degeneration(self) -> Tuple['Pattern', bool]:
        """removes unnessescary complex hierarchies of patterns. the definition
        of degeneration is given by the concrete pattern type. for example,
        a list with only one element is degenerated and is replaced by its
        subpattern.

        Returns:
            (Pattern, True) if the pattern has been changed
            otherwise (Pattern, False)
        """
        pass

    def remove_activity(self, activity: str) -> bool:
        """removes an activity (singleton) in this pattern and in its subpatterns.
        Returns True iff the activity was part of this pattern and has been
        removed.
        """
        changed = self._remove_activity(activity)
        if changed:
            self.__cached_activity_set = None
            self.__cached_activity_name = None
            self.__cached_start_activities = None
            self.__cached_end_activities = None
            self.__cached_hash = None
        return changed

    @abstractmethod
    def _remove_activity(self, activity: str) -> bool:
        """removes an activity (singleton) in this pattern and in its subpatterns

        Returns:
            True if the pattern has been changed, i.e. the given activity was
            part of this pattern
        """
        pass

    def merge_subpatterns(self) -> bool:
        """merges redundant subpattern into this pattern, e.g. if a sequence
        contains subsequences, the subsequence elements are added to the sequence
        and the subsequence is removed"""
        changed = self._merge_subpatterns()
        if changed:
            self.__cached_activity_name = None
            self.__cached_hash = None
        return changed

    @abstractmethod
    def _merge_subpatterns(self) -> bool:
        """merges redundant subpattern into this pattern, e.g. if a sequence
        contains subsequences, the subsequence elements are added to the sequence
        and the subsequence is removed

        Returns:
            True iff the pattern has been changed by this operation
        """
        pass

    def copy(self) -> 'Pattern':
        """returns a copy of this pattern"""
        copy = self._copy()
        copy.__cached_activity_name = self.__cached_activity_name
        copy.__cached_activity_set = self.__cached_activity_set
        copy.__cached_hash = self.__cached_hash
        copy.__cached_start_activities = self.__cached_start_activities
        copy.__cached_end_activities = self.__cached_end_activities
        return copy

    def clear_cache(self, recursive: bool = False):
        self.__cached_activity_set = None
        self.__cached_activity_name = None
        self.__cached_start_activities = None
        self.__cached_end_activities = None
        self.__cached_hash = None
        if recursive:
            for subpattern in self.get_subpatterns():
                subpattern.clear_cache(recursive=True)

    @abstractmethod
    def _copy(self) -> 'Pattern':
        """returns a copy of this pattern"""
        pass

    def is_singleton(self) -> bool:
        return self.get_nr_of_subpatterns() == 0

    def is_optional(self) -> bool:
        """returns True iff this pattern is of type Optional"""
        return False

    def __hash__(self):
        if self.__cached_hash is None:
            self.__cached_hash = hash(self.get_activity_name())
        return self.__cached_hash

    def __repr__(self):
        return self.get_activity_name()

    def __eq__(self, other):
        return self is other or self.get_activity_name() == other.get_activity_name()

    @abstractmethod
    def add_to_petri_net(self, petri_net: DataPetriNet) -> Tuple[Place,Place]:
        """adds places and transitions to this petri net to rebuild this pattern.
        returns start place and end place created by this pattern"""
        pass

    def replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        """recursively replaces all occurences of the given singleton activity
        by a pattern. This method does not throw an Exception of the singleton
        does not occur in this pattern or its subpatterns. The returned pattern
        of this method is not a copy. non-singletons return themselves,
        singletons either return themselves or the given replacement pattern.
        """
        self.clear_cache()
        return self._replace_singleton(activity, pattern)

    @abstractmethod
    def _replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        """recursively replaces all occurences of the given singleton activity
        by a pattern. This method does not throw an Exception of the singleton
        does not occur in this pattern or its subpatterns. The returned pattern
        of this method is not a copy. non-singletons return themselves,
        singletons either return themselves or the given replacement pattern.
        """
        pass

    def replace_direct_subpattern(self, subpattern: 'Pattern',
                                  replacement: 'Pattern'):
        """replaces the given subpattern with the given replacement. the
        subpattern must be a direct child of this pattern, otherwise an error
        will be thrown
        """
        self._replace_direct_subpattern(subpattern, replacement)
        self.clear_cache()

    @abstractmethod
    def _replace_direct_subpattern(self, subpattern: 'Pattern',
                                   replacement: 'Pattern'):
        """replaces the given subpattern with the given replacement. the
        subpattern must be a direct child of this pattern, otherwise an error
        will be thrown. "clear_cache" needs not to be called, because this
        is handled by the superclass.
        """
        pass

    def start_activities(self) -> Set[str]:
        """returns a set of activities that must be visited first
        during a complete cover of the pattern. for performance reasons,
        this method caches its result, i.e. a pattern should not have been
        changed during two successive calls of this method. public methods of
        the pattern class that change the internal structure
        (e.g. replace_singleton()) reset the cache and are thus safe to use.
        """
        if self.__cached_start_activities is None:
            self.__cached_start_activities = self._start_activities()
        return self.__cached_start_activities

    @abstractmethod
    def _start_activities(self) -> Set[str]:
        """returns a set of activities that must be visited first
        during a complete cover of the pattern
        """
        pass

    def end_activities(self) -> Set[str]:
        """returns a set of activities that must be visited eventually
        during a complete cover of the pattern. for performance reasons,
        this method caches its result, i.e. a pattern should not have been
        changed during two successive calls of this method. public methods of
        the pattern class that change the internal structure
        (e.g. replace_singleton()) reset the cache and are thus safe to use.
        """
        if self.__cached_end_activities is None:
            self.__cached_end_activities = self._end_activities()
        return self.__cached_end_activities

    @abstractmethod
    def _end_activities(self) -> Set[str]:
        """returns a set of activities that must be visited eventually
        during a complete cover of the pattern
        """
        pass

    @abstractmethod
    def generate_activities(self, random: Random = None) -> List[str]:
        """method for log generation"""
        pass
