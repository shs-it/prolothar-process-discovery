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
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph, Node
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet

from typing import List, Set, Union

NR_OF_PATTERN_TYPES_WITH_SINGLETON = 9
NR_OF_PATTERN_TYPES_WITHOUT_SINGLETON = NR_OF_PATTERN_TYPES_WITH_SINGLETON - 1

from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern

class PatternDfg(DirectlyFollowsGraph):
    """extends DirectlyFollowsGraph by the concept of patterns. Each node in
    the graph can have a sequential pattern of activities representing a
    subgraph. That means, a PatternDfg can be a compressed version of a larger
    and more complex DirectlyFollowsGraph"""

    def __init__(self): ...

    def add_node(self, activity: str): ...

    def add_pattern(self, activity: str, pattern: Pattern):
        """sets the pattern of the node with the given activity. this activity
        node must exist in the graph. otherwise a KeyError is raised"""
        ...

    def expand(self, recursive: bool = True) -> DirectlyFollowsGraph:
        """sets all counts to 0 such that one can restore the counts with a log
        by using the add_count method after calling this method
        """
        ...

    def fold(self, patterns: Set[Pattern]) -> 'PatternDfg':
        ...

    def get_patterns_with_activity(self, activity: str) -> List[Pattern]:
        ...

    def find_node_containing_activity(self, activity: str) -> Node:
        """returns the first node found which has a pattern that contains the
        given activity"""
        ...

    def copy(self) -> 'PatternDfg':
        """creates a copy of this graph"""
        ...

    def to_nested_graph(self, log : EventLog = None) -> NestedGraph:
        """optional parameter "log" is used to determine "shadow" activities,
        i.e. activities in the pattern-dfg, which are not part of the log, but
        were introduced artificially for better structure in the graph
        """
        ...

    def remove_degenerated_patterns(self):
        """removes unnessescary complex hierarchies of patterns. the definition
        of degeneration is given by the concrete pattern type. for example,
        a list with only one element is degenerated and is replaced by its
        subpattern.
        """
        ...

    def contains_non_singleton_pattern(self) -> bool:
        """returns True if at least one of the nodes in the graph has a
        non-singleton pattern"""
        ...

    def convert_to_petri_net(self) -> DataPetriNet:
        """converts this pattern graph to a petri net"""
        ...

    def compute_activity_set(self) -> Set[str]:
        """returns all low level activities in this graph"""
        ...

    def get_coverable_activities(self, activity: str) -> Set[str]:
        """from a given high-level activity, this method returns the set
        of start activities of the patterns of the nodes that directly-follow
        the given high-level activity node
        """
        ...

    def generate_log(
            self, nr_of_traces: int, random_seed = None,
            start_activities: Union[Set[str],List[str]] = None,
            end_activities: Union[Set[str],List[str]] = None) -> EventLog:
        """samples sequences from the directly-follows-graph.

        Args:
            nr_of_traces:
                nr of traces in the log that should be generated. must be > 0
            random_seed:
                default is None. can be set to a fixed value for reproducible
                results.

        Raises:
            ValueError:
                if the list of start_activities or end_activities is empty
        """
        ...

    def remove_singleton(self, activity: str, create_connections: bool = False):
        """if the given activity is part of a pattern, the activity will be
        removed from the pattern. if the pattern becomes empty by this, then
        the node will be removed. preceding and following nodes of the removed
        node will be connected

        Args:
            - activity:
                the singleton activity that is supposed to be removed
            - create_connections:
                default is False. Only relevant if the singleton is a node in
                the graph. This parameter controls if the preceding activities
                of the given activity will be connected to the following
                activities when removing the node.
        """
        ...

    @staticmethod
    def create_from_event_log(log: EventLog) -> 'PatternDfg':
        ...

    @staticmethod
    def create_from_dfg(dfg: DirectlyFollowsGraph) -> 'PatternDfg':
        """converts a DirectlyFollowsGraph into a PatternDfg. Each node of
        the PatternDfg will be a singleton pattern. if the given dfg already is
        a PatternDfg, then a copy will be returned."""
        ...

    @staticmethod
    def create_from_nested_graph(graph: NestedGraph) -> 'PatternDfg':
        """
        converts the NestedGraph - that should have been created with
        "PatternDfg.to_nested_graph" - back into the PatternDfg
        """
        ...

    @staticmethod
    def of_pattern(pattern: Pattern) -> 'PatternDfg':
        """create a PatternDfg with only one node with the given pattern"""
        ...
