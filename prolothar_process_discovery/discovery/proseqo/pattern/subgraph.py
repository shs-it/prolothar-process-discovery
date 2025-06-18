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

from prolothar_common.models.eventlog import EventLog, Trace
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_common.models.dfg.node import Node

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import NR_OF_PATTERN_TYPES_WITH_SINGLETON
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Transition, Place

from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_subgraph import CoveringSubGraph

import prolothar_common.mdl_utils as mdl_utils
from math import log2

from random import Random

from typing import Set, List, Tuple

class SubGraph(Pattern):
    """A subgraph of a PatternDfg"""

    def __init__(self, pattern_dfg: PatternDfg, start_activities: List[str],
                 end_activities: List[str]):
        """creats a new subgraph pattern

        Args:
            pattern_dfg:
                the PatternDfg of the subgraph
            start_activities:
                a list of start_activities to which preceding activities can
                be connected
            end_activities:
                a list of start_activities to which following activities can
                be connected
        """
        super().__init__()
        if pattern_dfg.get_nr_of_nodes() == 0:
            raise ValueError('pattern_dfg must not be empty')
        self.pattern_dfg = pattern_dfg
        self.set_start_activities(start_activities)
        self.set_end_activities(end_activities)
        self.__shortest_path_cache = {}
        self.__rebuild_activities_node_cache()

    def __rebuild_activities_node_cache(self):
        self.__activities_node_dict = {}
        for node in self.pattern_dfg.get_nodes():
            for activity in node.pattern.get_activity_set():
                self.__activities_node_dict[activity] = node

    def set_start_activities(self, start_activities: List[str]):
        start_activities = list(start_activities)
        for activity in start_activities:
            if activity not in self.pattern_dfg.nodes:
                raise ValueError(
                        'start activity "%s" not in pattern_dfg' % activity)
        for source in self.pattern_dfg.get_source_activities():
            if source not in start_activities:
                start_activities.append(source)
        if not start_activities:
            raise ValueError('start activities must not be empty')
        self.__start_activities = start_activities
        self.clear_cache()

    def set_end_activities(self, end_activities: List[str]):
        end_activities = list(end_activities)
        for activity in end_activities:
            if activity not in self.pattern_dfg.nodes:
                raise ValueError(
                        'end activity "%s" not in pattern_dfg' % activity)
        for sink in self.pattern_dfg.get_sink_activities():
            if sink not in end_activities:
                end_activities.append(sink)
        if not end_activities:
            raise ValueError('end activities must not be empty')
        self.__end_activities = end_activities
        self.clear_cache()

    def _generate_activity_name(self) -> str:
        if self.pattern_dfg.get_nr_of_nodes() > 1:
            return '[{%s},...,{%s}]' % (
                    ','.join(self.__start_activities),
                    ','.join(self.__end_activities))
        else:
            return '[%s]' % next(iter(self.pattern_dfg.get_nodes())).activity

    def get_nr_of_subpatterns(self) -> int:
        return self.pattern_dfg.get_nr_of_nodes()

    def get_subpatterns(self) -> List[Pattern]:
        return [node.pattern for node in self.pattern_dfg.get_nodes()]

    def expand_dfg(self, node: Node, dfg: DirectlyFollowsGraph,
                   recursive: bool = True):
        preceeding_activities = dfg.get_preceeding_activities(node.activity)
        following_activities = dfg.get_following_activities(node.activity)

        dfg.remove_node(node.activity)
        need_to_handle_selfloop = [edge for edge in node.edges \
                                   if edge.end.activity == node.activity]

        for subnode in self.pattern_dfg.get_nodes():
            dfg.add_node(subnode.pattern.get_activity_name())

        for preceeding_activity in preceeding_activities:
            for start_activity in self.__start_activities:
                if preceeding_activity != start_activity:
                    dfg.add_count(preceeding_activity, start_activity)

        self._expand_dfg_handle_outgoing_edges(following_activities, dfg,
                                               need_to_handle_selfloop)

        for edge in self.pattern_dfg.get_edges():
            dfg.add_count(edge.start.activity, edge.end.activity)

        for subnode in self.pattern_dfg.get_nodes():
            if recursive:
                subnode.pattern.expand_dfg(dfg.nodes[subnode.pattern.get_activity_name()], dfg)
            else:
                dfg.add_pattern(subnode.pattern.get_activity_name(), subnode.pattern)

    def _expand_dfg_handle_outgoing_edges(self, following_activities,
                                          dfg, need_to_handle_selfloop):
        for following_activity in following_activities:
            for end_activity in self.__end_activities:
                if following_activity != end_activity:
                    dfg.add_count(end_activity, following_activity)

        if need_to_handle_selfloop:
            for start_activity in self.__start_activities:
                for end_activity in self.__end_activities:
                    dfg.add_count(end_activity, start_activity)

    def fold_dfg(self, dfg: PatternDfg):
        if self.get_activity_name() in dfg.nodes:
            return

        dfg.add_node(self.get_activity_name())

        for node in self.pattern_dfg.get_nodes():
            if node.pattern is not None:
                node.pattern.fold_dfg(dfg)

        pattern_dfg = self.pattern_dfg.copy()
        self._fold_dfg_handle_preceding_activities(pattern_dfg, dfg)

        self._fold_dfg_handle_following_activities(pattern_dfg, dfg)

        for node in pattern_dfg.get_nodes():
            dfg.remove_node(node.activity)

        dfg.remove_edge((self.get_activity_name(), self.get_activity_name()))

        dfg.nodes[self.get_activity_name()].pattern = self

    def _fold_dfg_handle_preceding_activities(self, pattern_dfg: PatternDfg,
                                              dfg: PatternDfg):
        preceeding_activities = set()

        for start_activity in self.__start_activities:
            preceeding_activities = preceeding_activities.union(
                    dfg.get_preceeding_activities(start_activity))
        for activity in preceeding_activities:
            dfg.add_count(activity, self.get_activity_name())

    def _fold_dfg_handle_following_activities(self, pattern_dfg: PatternDfg,
                                              dfg: PatternDfg):
        following_activities = set()
        for end_activity in self.__end_activities:
            following_activities = following_activities.union(
                    dfg.get_following_activities(end_activity))
        for activity in following_activities:
            dfg.add_count(self.get_activity_name(), activity)

    def get_encoded_length_in_code_table(
            self, available_activities: Set[str]) -> Tuple[float,Set[str]]:
        #encode number of nodes
        encoded_length = log2(len(available_activities))
        encoded_length += (self.pattern_dfg.get_nr_of_nodes() *
                           log2(NR_OF_PATTERN_TYPES_WITH_SINGLETON))
        if encoded_length < 0:
            raise ValueError(self.pattern_dfg)
        #encoding of start and end nodes, sources/sinks are set as start/end nodes
        nr_of_sources = len(self.pattern_dfg.get_source_activities())
        nr_of_sinks = len(self.pattern_dfg.get_sink_activities())
        nr_of_possible_starts = self.pattern_dfg.get_nr_of_nodes() - nr_of_sources
        nr_of_possible_ends = self.pattern_dfg.get_nr_of_nodes() - nr_of_sinks
        encoded_length += log2(nr_of_possible_starts + 1)
        encoded_length += log2(nr_of_possible_ends + 1)
        if encoded_length < 0:
            raise ValueError()
        encoded_length += mdl_utils.log2binom(
                nr_of_possible_starts, len(self.__start_activities) - nr_of_sources)
        encoded_length += mdl_utils.log2binom(
                nr_of_possible_ends, len(self.__end_activities) - nr_of_sinks)
        if encoded_length < 0:
            raise ValueError()
        #encoding of subpatterns
        for node in self.pattern_dfg.get_nodes():
            code_length_of_node, available_activities = \
                node.pattern.get_encoded_length_in_code_table(
                    available_activities)
            encoded_length += code_length_of_node
        #nr of edges
        encoded_length += log2(1 + self.pattern_dfg.get_nr_of_nodes() ** 2)
        #where are the edges
        encoded_length += mdl_utils.log2binom(self.pattern_dfg.get_nr_of_nodes() ** 2,
                                              self.pattern_dfg.get_nr_of_edges())
        return encoded_length, available_activities

    def for_covering(self, trace, last_covered_activity: str):
        return CoveringSubGraph(self, trace, last_covered_activity)

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str):
        nr_of_nodes = 0
        activity_to_id = {}
        for pattern in self.get_subpatterns():
            pattern_id = base_id + '.' + str(nr_of_nodes)
            graph.add_node(pattern.create_node_for_nested_graph(
                    pattern_id, parent_id=base_id))
            pattern.add_subpatterns_to_nested_graph(graph, pattern_id)
            activity_to_id[pattern.get_activity_name()] = pattern_id
            nr_of_nodes += 1

        for edge in self.pattern_dfg.get_edges():
            source = str(activity_to_id[edge.start.activity])
            target = str(activity_to_id[edge.end.activity])
            graph.add_edge(NestedGraph.Edge(
                    source + '->' + target, source, target))

    def _without_degeneration(self):
        """ a community is degenerated if there is only one node
        """
        if self.get_nr_of_subpatterns() == 1:
            return self.get_subpatterns()[0].without_degeneration()[0], True
        else:
            changed = False
            for node in self.pattern_dfg.get_nodes():
                changed = self.__without_degeneration_for_node(node) or changed

            return self, changed

    def __without_degeneration_for_node(self, node):
        node.pattern, changed = node.pattern.without_degeneration()
        new_activity_name = node.pattern.get_activity_name()
        if node.activity != new_activity_name:
            if node.activity in self.__start_activities:
                self.__start_activities.remove(node.activity)
                self.pattern_dfg.rename_activity(node.activity,
                                                 new_activity_name)
                self.__start_activities.append(new_activity_name)
            elif node.activity in self.__end_activities:
                self.__end_activities.remove(node.activity)
                self.pattern_dfg.rename_activity(node.activity,
                                                 new_activity_name)
                self.__end_activities.append(new_activity_name)
            else:
                self.pattern_dfg.rename_activity(node.activity,
                                                 new_activity_name)
        return changed

    def _merge_subpatterns(self):
        changed = False
        for node in self.pattern_dfg.get_nodes():
            if node.pattern.merge_subpatterns():
                changed = True
            node.activity = node.pattern.get_activity_name()
            if isinstance(node.pattern, SubGraph):
                raise NotImplementedError()
        return changed

    def _remove_activity(self, activity: str):
        activities_for_removal = []
        rename_activities = []
        for node in list(self.pattern_dfg.get_nodes()):
            if node.pattern.is_singleton() and node.pattern.contains_activity(
                    activity):
                activities_for_removal.append(node.activity)
            else:
                node.pattern.remove_activity(activity)
                rename_activities.append(
                        (node.activity, node.pattern.get_activity_name()))
        for a in activities_for_removal:
            self.pattern_dfg.remove_node(a)
            try:
                self.__start_activities.remove(a)
            except ValueError:
                pass
            try:
                self.__end_activities.remove(a)
            except ValueError:
                pass
        for old_activity, new_activity in rename_activities:
            if old_activity != new_activity:
                self.pattern_dfg.rename_activity(old_activity, new_activity)
                self.__start_activities = [
                    a if a != old_activity else new_activity
                    for a in self.__start_activities
                ]
                self.__end_activities = [
                    a if a != old_activity else new_activity
                    for a in self.__end_activities
                ]
        if self.get_nr_of_subpatterns() == 0:
            raise ValueError('Community must not be empty')
        changed = activities_for_removal or rename_activities
        if changed:
            self.__rebuild_activities_node_cache()

    def create_cut_log_from_community(self, log: EventLog) -> EventLog:
        """returns an event log with cut traces, i.e. activities occuring before
        and after the community are removed"""
        cut_log = EventLog()
        community_activities = self.get_activity_set()
        for trace in log.traces:
            cut_trace = []
            community_started = False
            for i,event in enumerate(trace.events):
                community_started = community_started or event.activity_name in community_activities
                if community_started:
                    if event.activity_name not in community_activities and not [
                            e for e in trace.events[i:]
                            if e.activity_name in community_activities]:
                        break
                    cut_trace.append(event)
            cut_log.add_trace(Trace(trace.get_id(), cut_trace,
                                    attributes=trace.attributes))
        return cut_log

    def add_to_petri_net(self, petri_net: DataPetriNet):
        start_places = {}
        end_places = {}
        global_start_place = petri_net.add_place(Place.with_empty_label(
                '__start__' + self.get_activity_name()))
        global_end_place = petri_net.add_place(Place.with_empty_label(
                '__end__' + self.get_activity_name()))
        for node in self.pattern_dfg.get_nodes():
            start_place, end_place = node.pattern.add_to_petri_net(petri_net)
            start_places[node.activity] = start_place
            end_places[node.activity] = end_place
            if node.activity in self.__start_activities:
                transition = petri_net.add_transition(Transition(
                        '__startwith__' + node.activity, visible=False))
                petri_net.add_connection(global_start_place, transition, start_place)
            if node.activity in self.__end_activities:
                transition = petri_net.add_transition(Transition(
                        '__endwith__' + node.activity, visible=False))
                petri_net.add_connection(end_place, transition, global_end_place)
        for edge in self.pattern_dfg.get_edges():
            transition = petri_net.add_transition(Transition(
                    edge.start.activity + '->' + edge.end.activity, visible=False))
            petri_net.add_connection(end_places[edge.start.activity],
                                     transition,
                                     start_places[edge.end.activity])
        return global_start_place, global_end_place

    def _copy(self) -> 'Pattern':
        return SubGraph(self.pattern_dfg.copy(),
                        list(self.__start_activities),
                        list(self.__end_activities))

    def _replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        for node in self.pattern_dfg.get_nodes():
            node.pattern = node.pattern.replace_singleton(activity, pattern)
        return self

    def _replace_direct_subpattern(self, subpattern: 'Pattern',
                                   replacement: 'Pattern'):
        self.pattern_dfg.add_pattern(subpattern.get_activity_name(), replacement)
        self.pattern_dfg.rename_activity(
                subpattern.get_activity_name(), replacement.get_activity_name())
        self.__rebuild_activities_node_cache()

    def get_nr_of_forbidden_edges_in_pattern_dfg(
            self, pattern_dfg: DirectlyFollowsGraph) -> int:
        return 0

    def _start_activities(self) -> Set[str]:
        start_activities = set()
        for activity in self.__start_activities:
            start_activities.update(self.pattern_dfg.nodes[
                    activity].pattern.start_activities())
        return start_activities

    def _end_activities(self) -> Set[str]:
        end_activities = set()
        for activity in self.__end_activities:
            try:
                end_activities.update(self.pattern_dfg.nodes[
                        activity].pattern.end_activities())
            except KeyError as e:
                print(activity)
                self.pattern_dfg.plot()
                raise e
        return end_activities

    def get_start_subpatterns(self) -> List['Pattern']:
        return [self.pattern_dfg.nodes[activity].pattern
                for activity in self.__start_activities]

    def get_start_activities(self) -> List[str]:
        return self.__start_activities

    def get_end_activities(self) -> List[str]:
        return self.__end_activities

    def get_end_subpatterns(self) -> List['Pattern']:
        return [self.pattern_dfg.nodes[activity].pattern
                for activity in self.__end_activities]

    def generate_activities(self, random: Random = None) -> List[str]:
        activities = []
        current_node = None
        next_possible_nodes = [self.pattern_dfg.nodes[a] for a in self.__start_activities]
        while True:
            current_node = random.choice(next_possible_nodes)
            next_possible_nodes = [edge.end for edge in current_node.edges]
            for activity in current_node.pattern.generate_activities(
                    random=random):
                activities.append(activity)
            if current_node.activity in self.__end_activities:
                break
        return activities

    def compute_shortest_path(self, start: str, end: str):
        cache_key = (start, end)
        if not cache_key in self.__shortest_path_cache:
            shortest_path = self.pattern_dfg.compute_shortest_path(start, end)
            self.__shortest_path_cache[cache_key] = shortest_path
            return shortest_path
        else:
            return self.__shortest_path_cache[cache_key]

    def find_node_containing_activity(self, activity: str):
        try:
            return self.__activities_node_dict[activity]
        except KeyError:
            return None