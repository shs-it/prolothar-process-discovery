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

from prolothar_common.models.eventlog import EventLog, Trace, Event
from prolothar_common.models.dfg.edge cimport Edge
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Transition

from typing import List, Set, Union

NR_OF_PATTERN_TYPES_WITH_SINGLETON = 9
NR_OF_PATTERN_TYPES_WITHOUT_SINGLETON = NR_OF_PATTERN_TYPES_WITH_SINGLETON - 1

from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_process_discovery.discovery.proseqo.pattern.loop import Loop
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional

from random import Random

cdef class PatternDfg(DirectlyFollowsGraph):
    """extends DirectlyFollowsGraph by the concept of patterns. Each node in
    the graph can have a sequential pattern of activities representing a
    subgraph. That means, a PatternDfg can be a compressed version of a larger
    and more complex DirectlyFollowsGraph"""

    def __init__(self):
        super().__init__()

    cpdef add_node(self, str activity):
        DirectlyFollowsGraph.add_node(self, activity)
        cdef Node added_node = self.nodes[activity]
        if added_node.pattern is None:
            added_node.pattern = Singleton(activity)

    cpdef add_pattern(self, str activity, Pattern pattern):
        """sets the pattern of the node with the given activity. this activity
        node must exist in the graph. otherwise a KeyError is raised"""
        (<Node>self.nodes[activity]).pattern = pattern

    def expand(self, recursive: bool = True) -> DirectlyFollowsGraph:
        """sets all counts to 0 such that one can restore the counts with a log
        by using the add_count method after calling this method
        """
        expanded_dfg = self.copy()
        for node in self.nodes.values():
            node.pattern.expand_dfg(
                    expanded_dfg.nodes[node.activity], expanded_dfg,
                    recursive=recursive)

        for edge in expanded_dfg.edges.values():
            edge.count = 0

        return expanded_dfg

    def fold(self, patterns: Set[Pattern]) -> 'PatternDfg':
        folded_dfg = self.copy()
        for pattern in patterns:
            pattern.fold_dfg(folded_dfg)
        return folded_dfg

    cpdef list get_patterns_with_activity(self, str activity):
        cdef list matching_patterns = []
        for node in self.nodes.values():
            if (<Pattern>(<Node>node).pattern).contains_activity(activity):
                matching_patterns.append((<Node>node).pattern)
        return matching_patterns

    cpdef Node find_node_containing_activity(self, str activity):
        """returns the first node found which has a pattern that contains the
        given activity"""
        for node in self.nodes.values():
            if (<Pattern>(<Node>node).pattern).contains_activity(activity):
                return node

    cpdef PatternDfg copy(self):
        """creates a copy of this graph"""
        cdef PatternDfg copy = PatternDfg()
        copy.join(self)
        cdef Node node
        for node in self.nodes.values():
            copy.add_pattern(
                node.activity, 
                (<Pattern>node.pattern).copy()
            )
        return copy

    def to_nested_graph(self, log : EventLog = None) -> NestedGraph:
        """optional parameter "log" is used to determine "shadow" activities,
        i.e. activities in the pattern-dfg, which are not part of the log, but
        were introduced artificially for better structure in the graph
        """
        return _create_nested_graph_with_high_level_edges(self, log=log)

    cpdef remove_degenerated_patterns(self):
        """removes unnessescary complex hierarchies of patterns. the definition
        of degeneration is given by the concrete pattern type. for example,
        a list with only one element is degenerated and is replaced by its
        subpattern.
        """
        cdef Node node
        for node in list(self.get_nodes()):
            node.pattern, _ = node.pattern.without_degeneration()
            #through removal of degenerated patterns, we can have broken
            #activity names
            if node.activity != (<Pattern>node.pattern).get_activity_name():
                self.rename_activity(node.activity, (<Pattern>node.pattern).get_activity_name())

        for node in list(self.get_nodes()):
            node.pattern.merge_subpatterns()
            if node.activity != (<Pattern>node.pattern).get_activity_name():
                self.rename_activity(node.activity, (<Pattern>node.pattern).get_activity_name())

    def contains_non_singleton_pattern(self) -> bool:
        """returns True if at least one of the nodes in the graph has a
        non-singleton pattern"""
        for node in self.get_nodes():
            if not node.pattern.is_singleton():
                return True
        return False

    def convert_to_petri_net(self) -> DataPetriNet:
        """converts this pattern graph to a petri net"""
        petri_net = DataPetriNet()
        start_places = {}
        end_places = {}
        for node in self.get_nodes():
            start_place, end_place = node.pattern.add_to_petri_net(petri_net)
            start_places[node.activity] = start_place
            end_places[node.activity] = end_place
        for edge in self.get_edges():
            transition = petri_net.add_transition(Transition(
                    edge.start.activity + '->' + edge.end.activity, visible=False))
            petri_net.add_connection(end_places[edge.start.activity],
                                     transition,
                                     start_places[edge.end.activity])
        petri_net.prune()
        return petri_net

    cpdef set compute_activity_set(self):
        """returns all low level activities in this graph"""
        cdef set activity_set = set()
        for node in self.get_nodes():
            activity_set.update((<Pattern>(<Node>node).pattern).get_activity_set())
        return activity_set

    cpdef set get_coverable_activities(self, str activity):
        """from a given high-level activity, this method returns the set
        of start activities of the patterns of the nodes that directly-follow
        the given high-level activity node
        """
        cdef set coverable_activities = set()
        for edge in self.nodes[activity].edges:
            coverable_activities.update((<Pattern>(<Edge>edge).end.pattern).start_activities())
        return coverable_activities

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
        random_generator = Random(random_seed)
        if start_activities is not None:
            start_nodes = [self.nodes[a] for a in start_activities]
        else:
            start_nodes = self.get_source_nodes()
        if end_activities is None:
            end_activities = self.get_sink_activities()
        if not start_nodes:
            raise ValueError('start nodes  must not be empty')
        if not end_activities:
            raise ValueError('end activities must not be empty')
        log = EventLog()
        for i in range(nr_of_traces):
            events_in_trace = []
            current_node = None
            next_possible_nodes = start_nodes
            while next_possible_nodes:
                current_node = random_generator.choice(next_possible_nodes)
                next_possible_nodes = [edge.end for edge in current_node.edges]
                for activity in current_node.pattern.generate_activities(
                        random=random_generator):
                    events_in_trace.append(Event(activity))
                if current_node.activity in end_activities:
                    break
            log.add_trace(Trace(i, events_in_trace))
        return log

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
        for node in list(self.get_nodes()):
            try:
                if node.pattern.remove_activity(activity):
                    node.pattern.merge_subpatterns()
                    self.rename_activity(
                            node.activity, node.pattern.get_activity_name())
                    break
            except ValueError:
                self.remove_node(node.activity,
                                 create_connections=create_connections)
                break

    @staticmethod
    def create_from_event_log(log: EventLog) -> 'PatternDfg':
        dfg = PatternDfg()
        dfg.read_counts_from_log(log)
        return dfg

    @staticmethod
    def create_from_dfg(dfg: DirectlyFollowsGraph) -> 'PatternDfg':
        """converts a DirectlyFollowsGraph into a PatternDfg. Each node of
        the PatternDfg will be a singleton pattern. if the given dfg already is
        a PatternDfg, then a copy will be returned."""
        if isinstance(dfg, PatternDfg):
            return dfg.copy()
        pattern_dfg = PatternDfg()
        pattern_dfg.join(dfg)
        return pattern_dfg

    @staticmethod
    def create_from_nested_graph(graph: NestedGraph) -> 'PatternDfg':
        """
        converts the NestedGraph - that should have been created with
        "PatternDfg.to_nested_graph" - back into the PatternDfg
        """
        pattern_dfg = PatternDfg()
        for node in graph.get_nodes():
            if not node.parent:
                pattern_dfg.add_node(node.label)
                pattern_dfg.add_pattern(
                    node.label, PatternDfg.__parse_pattern_from_nested_graph_node(node, graph))
        for edge in graph.get_edges():
            #only high level edges have attributes
            if edge.attributes and edge.attributes['count'] is not None:
                pattern_dfg.add_count(
                    graph.get_node_by_id(edge.source).label,
                    graph.get_node_by_id(edge.target).label,
                    count=edge.attributes['count'])

        return pattern_dfg

    @staticmethod
    def __parse_pattern_from_nested_graph_node(
            node: NestedGraph.Node, graph: NestedGraph) -> Pattern:
        def parse_node_id(nested_node: NestedGraph.Node):
            return tuple(int(id_part) for id_part in nested_node.id.split('.'))
        pattern_type = node.attributes['pattern_type']
        if pattern_type == 'Singleton':
            return Singleton(node.label)
        elif pattern_type == 'Sequence':
            return Sequence([
                PatternDfg.__parse_pattern_from_nested_graph_node(child, graph)
                for child in sorted(
                    graph.get_children(node.id),
                    key=parse_node_id)
            ])
        elif pattern_type == 'Choice':
            return Choice([
                PatternDfg.__parse_pattern_from_nested_graph_node(child, graph)
                for child in graph.get_children(node.id)
            ])
        elif pattern_type == 'Loop':
            return Loop(
                PatternDfg.__parse_pattern_from_nested_graph_node(
                    next(iter(graph.get_children(node.id))), graph))
        elif pattern_type == 'Optional':
            return Optional(
                PatternDfg.__parse_pattern_from_nested_graph_node(
                    next(iter(graph.get_children(node.id))), graph))
        else:
            raise NotImplementedError('Unknown pattern type: %s' % pattern_type)

    @staticmethod
    def of_pattern(pattern: Pattern) -> 'PatternDfg':
        """create a PatternDfg with only one node with the given pattern"""
        pattern_dfg = PatternDfg()
        pattern_dfg.add_node(pattern.get_activity_name())
        pattern_dfg.add_pattern(pattern.get_activity_name(), pattern)
        return pattern_dfg

def _create_nested_graph_with_high_level_edges(dfg: PatternDfg, log=None) -> NestedGraph:
    graph = NestedGraph()
    nr_of_nodes = 0
    activity_to_id = {}
    for node in dfg.get_nodes():
        graph.add_node(node.pattern.create_node_for_nested_graph(str(nr_of_nodes)))
        node.pattern.add_subpatterns_to_nested_graph(graph, str(nr_of_nodes))
        activity_to_id[node.activity] = nr_of_nodes
        nr_of_nodes += 1

    for edge in dfg.get_edges():
        source = str(activity_to_id[edge.start.activity])
        target = str(activity_to_id[edge.end.activity])
        graph.add_edge(NestedGraph.Edge(
                source + '->' + target, source, target,
                {'count': edge.count}))

    return graph
