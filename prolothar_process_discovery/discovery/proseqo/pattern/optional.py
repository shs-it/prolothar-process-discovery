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
from collections import Counter

from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_common.models.dfg.node import Node

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import NR_OF_PATTERN_TYPES_WITH_SINGLETON
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Transition, Place

from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_optional import CoveringOptional

from math import log2

from random import Random

class Optional(Pattern):
    def __init__(self, opt_pattern: Pattern):
        super().__init__()
        self.opt_pattern = opt_pattern

    def expand_dfg(self, node: Node, dfg: DirectlyFollowsGraph,
                   recursive: bool = True):
        need_to_handle_selfloop = False

        dfg.add_node(self.opt_pattern.get_activity_name())

        preceeding_activities = dfg.get_preceeding_activities(node.activity)
        following_activities = dfg.get_following_activities(node.activity)

        #handle ingoing edges
        for preceeding_activity in preceeding_activities:
            #handle self-loops. otherwise removed pattern would be added again
            if node.activity != preceeding_activity:
                dfg.add_count(preceeding_activity,
                              self.opt_pattern.get_activity_name())
            else:
                need_to_handle_selfloop = True

        #handle outgoing edges
        for following_activity in following_activities:
            if node.activity != following_activity:
                dfg.add_count(self.opt_pattern.get_activity_name(),
                              following_activity)

        #optional: allow skipping the activity = connect preceding and
        #following activities
        for preceeding_activity in preceeding_activities:
            for following_activity in following_activities:
                dfg.add_count(preceeding_activity, following_activity, count=0)

        if need_to_handle_selfloop:
            dfg.add_count(self.opt_pattern.get_activity_name(),
                          self.opt_pattern.get_activity_name())

        dfg.remove_node(node.activity)
        if recursive:
            self.opt_pattern.expand_dfg(dfg.nodes[self.opt_pattern.get_activity_name()], dfg)
        else:
            dfg.add_pattern(self.opt_pattern.get_activity_name(), self.opt_pattern)

    def get_subpattern(self) -> Pattern:
        return self.opt_pattern

    def get_start_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def get_end_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def fold_dfg(self, dfg: DirectlyFollowsGraph):
        if self.get_activity_name() not in dfg.nodes:
            dfg.add_node(self.get_activity_name())

            self.opt_pattern.fold_dfg(dfg)

        if self.opt_pattern.get_activity_name() in dfg.nodes:
            preceeding_activities = dfg.get_preceeding_activities(
                    self.opt_pattern.get_activity_name())
            following_activities = dfg.get_following_activities(
                    self.opt_pattern.get_activity_name())

            pre_skip_counts = Counter()
            post_skip_counts = Counter()
            for preceeding_activity in preceeding_activities:
                for following_activity in following_activities:
                    pre_skip_counts[preceeding_activity] += dfg.get_count(
                            preceeding_activity, following_activity)
                    post_skip_counts[following_activity] += dfg.get_count(
                            preceeding_activity, following_activity)
                    dfg.remove_edge((preceeding_activity, following_activity))

            for preceeding_activity in preceeding_activities:
                dfg.add_count(
                        preceeding_activity, self.get_activity_name(),
                        count = dfg.get_count(
                                    preceeding_activity,
                                    self.opt_pattern.get_activity_name()
                                ) + pre_skip_counts[preceeding_activity]
                )
            for following_activity in following_activities:
                dfg.add_count(
                        self.get_activity_name(), following_activity,
                        count = dfg.get_count(
                                    self.opt_pattern.get_activity_name(),
                                    following_activity
                                ) + post_skip_counts[following_activity]
                )

            dfg.remove_node(self.opt_pattern.get_activity_name())

        #should not happen but we want to assert that there is no connection
        #from predecessors to ancestors
        for preceding_activity in dfg.get_preceeding_activities(
                self.get_activity_name()):
            for following_activity in dfg.get_following_activities(
                self.get_activity_name()):
                if (preceding_activity, following_activity) in dfg.edges \
                and preceding_activity != following_activity:
                    dfg.remove_edge((preceding_activity, following_activity))

        dfg.nodes[self.get_activity_name()].pattern = self

    def _generate_activity_name(self) -> str:
        return self.opt_pattern.get_activity_name() + '?'

    def get_nr_of_subpatterns(self) -> int:
        return 1

    def get_subpatterns(self) -> List[Pattern]:
        return [self.opt_pattern]

    def get_encoded_length_in_code_table(
            self, available_activities: Set[str]) -> Tuple[float,Set[str]]:
        code_length_of_subpattern, available_activities = \
            self.opt_pattern.get_encoded_length_in_code_table(
                available_activities)
        return (log2(NR_OF_PATTERN_TYPES_WITH_SINGLETON) +
                code_length_of_subpattern, available_activities)

    def for_covering(self, trace, last_covered_activity: str):
        return CoveringOptional(self, trace, last_covered_activity)

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str):
        pattern_id = base_id + '.0'
        graph.add_node(self.opt_pattern.create_node_for_nested_graph(
                    pattern_id, parent_id=base_id))
        self.opt_pattern.add_subpatterns_to_nested_graph(graph, pattern_id)

    def _without_degeneration(self):
        """ an optional is degenerated if its subpattern is an optional, too
        """
        if isinstance(self.opt_pattern, Optional):
            return self.opt_pattern.without_degeneration()[0], True
        else:
            self.opt_pattern, changed = self.opt_pattern.without_degeneration()
            return self, changed

    def _merge_subpatterns(self):
        changed = self.opt_pattern.merge_subpatterns()
        if isinstance(self.opt_pattern, Optional):
            self.opt_pattern = self.opt_pattern.opt_pattern
            changed = True
        return changed

    def _remove_activity(self, activity: str):
        return self.opt_pattern.remove_activity(activity)

    def _copy(self) -> 'Pattern':
        return Optional(self.opt_pattern.copy())

    def add_to_petri_net(self, petri_net: DataPetriNet) -> Tuple[Place,Place]:
        transition_skip = petri_net.add_transition(Transition(
                    '__skip__' + self.opt_pattern.get_activity_name(),
                    visible=False))

        subpattern_pre_place, subpattern_post_place = \
            self.opt_pattern.add_to_petri_net(petri_net)

        petri_net.add_connection(
                subpattern_pre_place, transition_skip, subpattern_post_place)

        return subpattern_pre_place, subpattern_post_place

    def _replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        self.opt_pattern = self.opt_pattern.replace_singleton(activity, pattern)
        return self

    def _replace_direct_subpattern(self, subpattern: 'Pattern',
                                   replacement: 'Pattern'):
        if not self.opt_pattern == subpattern:
            raise ValueError()
        self.opt_pattern = replacement

    def get_nr_of_forbidden_edges_in_pattern_dfg(
            self, pattern_dfg: DirectlyFollowsGraph) -> int:
        #A => B? => C implies there is no edge from A to C
        return len(pattern_dfg.get_preceeding_activities(
                self.get_activity_name())) * len(
                        pattern_dfg.get_following_activities(
                                self.get_activity_name()))

    def generate_activities(self, random: Random = None) -> List[str]:
        if random is None:
            random = Random()
        if random.choice([True, False]):
            return self.opt_pattern.generate_activities(random=random)
        else:
            return []

    def _start_activities(self) -> Set[str]:
        return self.opt_pattern.start_activities()

    def _end_activities(self) -> Set[str]:
        return self.opt_pattern.end_activities()

    def is_optional(self):
        return True
