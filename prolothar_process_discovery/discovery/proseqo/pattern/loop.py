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

from typing import Tuple, Set, List

from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_common.models.dfg.node import Node

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import NR_OF_PATTERN_TYPES_WITH_SINGLETON
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Transition, Place

from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_loop import CoveringLoop

from math import log2

from random import Random

class Loop(Pattern):
    """implementation of a loop pattern, i.e. a pattern with exactly one
    subpattern that can be repeated infinitly many times"""

    def __init__(self, subpattern: Pattern):
        super().__init__()
        self.subpattern = subpattern

    def expand_dfg(self, node: Node, dfg: DirectlyFollowsGraph,
                   recursive: bool = True):
        dfg.add_node(self.subpattern.get_activity_name())
        dfg.add_count(self.subpattern.get_activity_name(),
                      self.subpattern.get_activity_name())

        preceeding_activities = dfg.get_preceeding_activities(node.activity)
        following_activities = dfg.get_following_activities(node.activity)

        #handle ingoing edges
        for preceeding_activity in preceeding_activities:
            #handle self-loops. otherwise removed pattern would be added again
            if node.activity != preceeding_activity:
                dfg.add_count(preceeding_activity,
                              self.subpattern.get_activity_name())

        #handle outgoing edges
        for following_activity in following_activities:
            if node.activity != following_activity:
                dfg.add_count(self.subpattern.get_activity_name(),
                              following_activity)

        dfg.remove_node(node.activity)
        if recursive:
            self.subpattern.expand_dfg(dfg.nodes[self.subpattern.get_activity_name()], dfg)
        else:
            dfg.add_pattern(self.subpattern.get_activity_name(), self.subpattern)

    def fold_dfg(self, dfg: DirectlyFollowsGraph):
        super().fold_dfg(dfg)
        dfg.remove_edge((self.get_activity_name(),
                         self.get_activity_name()))

    def _generate_activity_name(self) -> str:
        return self.subpattern.get_activity_name() + '+'

    def get_nr_of_subpatterns(self) -> int:
        return 1

    def get_subpatterns(self) -> List[Pattern]:
        return [self.subpattern]

    def get_start_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def get_end_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def get_encoded_length_in_code_table(
            self, available_activities: Set[str]) -> Tuple[float,Set[str]]:
        code_length_of_subpattern, available_activities = \
            self.subpattern.get_encoded_length_in_code_table(
                available_activities)
        return (log2(NR_OF_PATTERN_TYPES_WITH_SINGLETON) +
                code_length_of_subpattern, available_activities)

    def for_covering(self, trace, last_covered_activity: str):
        return CoveringLoop(self, trace, last_covered_activity)

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str):
        pattern_id = base_id + '.0'
        graph.add_node(self.subpattern.create_node_for_nested_graph(
                    pattern_id, parent_id=base_id))
        self.subpattern.add_subpatterns_to_nested_graph(graph, pattern_id)

    def _without_degeneration(self) -> Tuple[Pattern, bool]:
        """ a loop of a loop is degenerated"""
        if isinstance(self.subpattern, Loop):
            return self.subpattern.without_degeneration()[0], True
        else:
            self.subpattern, changed = self.subpattern.without_degeneration()
            return self, changed

    def _merge_subpatterns(self):
        changed = False
        if isinstance(self.subpattern, Loop):
            self.subpattern = self.subpattern.subpattern
            changed = True
        if (isinstance(self.subpattern, Sequence) and
            self.subpattern.get_nr_of_subpatterns() == 2 and
            isinstance(self.subpattern.get_subpatterns()[0], Loop) and
            isinstance(self.subpattern.get_subpatterns()[1], Optional)):
                self.subpattern = Sequence([
                        self.subpattern.get_subpatterns()[0].subpattern,
                        self.subpattern.get_subpatterns()[1]
                ])
                changed = True

        if self.subpattern.merge_subpatterns():
            changed = True
        return changed

    def _remove_activity(self, activity: str):
        return self.subpattern.remove_activity(activity)

    def _copy(self) -> 'Pattern':
        return Loop(self.subpattern.copy())

    def add_to_petri_net(self, petri_net: DataPetriNet) -> Tuple[Place,Place]:
        place_start = petri_net.add_place(Place.with_empty_label(
                '__startloop__' + self.subpattern.get_activity_name()))
        transition_start = petri_net.add_transition(Transition(
                    '__startloop__' + self.subpattern.get_activity_name(),
                    visible=False))

        transition_repeat = petri_net.add_transition(Transition(
                    '__repeatloop__' + self.subpattern.get_activity_name(),
                    visible=False))

        place_end = petri_net.add_place(Place.with_empty_label(
                '__endloop__' + self.subpattern.get_activity_name()))
        transition_end = petri_net.add_transition(Transition(
                    '__endloop__' + self.subpattern.get_activity_name(),
                    visible=False))

        subpattern_pre_place, subpattern_post_place = \
            self.subpattern.add_to_petri_net(petri_net)

        petri_net.add_connection(
                place_start, transition_start, subpattern_pre_place)
        petri_net.add_connection(
                subpattern_post_place, transition_repeat, subpattern_pre_place)
        petri_net.add_connection(
                subpattern_post_place, transition_end, place_end)

        return place_start, place_end

    def _replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        self.subpattern = self.subpattern.replace_singleton(activity, pattern)
        return self

    def _replace_direct_subpattern(self, subpattern: 'Pattern',
                                   replacement: 'Pattern'):
        if not self.subpattern == subpattern:
            raise ValueError()
        self.subpattern = replacement

    def get_nr_of_forbidden_edges_in_pattern_dfg(self, pattern_dfg) -> int:
        #A+ implies there is no edge from A+ to A+
        return 1

    def generate_activities(self, random: Random = None) -> List[str]:
        if random is None:
            random = Random()
        activities = self.subpattern.generate_activities(random=random)
        if random.choice([True, False]):
            return activities + self.generate_activities(random=random)
        else:
            return activities

    def _start_activities(self) -> Set[str]:
        return self.subpattern.start_activities()

    def _end_activities(self) -> Set[str]:
        return self.subpattern.end_activities()