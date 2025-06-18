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

from typing import List, Tuple, Set

from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_common.models.dfg.node import Node

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import NR_OF_PATTERN_TYPES_WITH_SINGLETON
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Transition, Place

from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_sequence import CoveringSequence

from math import log2
import prolothar_common.mdl_utils as mdl_utils

from random import Random

class Sequence(Pattern):
    def __init__(self, pattern_list: List[Pattern],
                 special_noise_set: Set[str]|None = None):
        super().__init__()
        self.pattern_list = pattern_list
        if special_noise_set is None:
            self.special_noise_set = set()
        else:
            self.special_noise_set = special_noise_set

    def expand_dfg(self, node: Node, dfg, recursive: bool = True):
        preceeding_activities = dfg.get_preceeding_activities(node.activity)
        following_activities = dfg.get_following_activities(node.activity)

        dfg.remove_node(node.activity)
        need_to_handle_selfloop = False
        for pattern in self.pattern_list:
            dfg.add_node(pattern.get_activity_name())
            #handle ingoing edges
            for preceeding_activity in preceeding_activities:
                #handle self-loops. otherwise removed pattern would be added again
                if node.activity != preceeding_activity:
                    dfg.add_count(preceeding_activity,
                                  pattern.get_activity_name())
                else:
                    need_to_handle_selfloop = True
            preceeding_activities = [pattern.get_activity_name()]
        #handle outgoing edges
        for following_activity in following_activities:
            if node.activity != following_activity:
                dfg.add_count(self.pattern_list[-1].get_activity_name(),
                              following_activity)

        if need_to_handle_selfloop:
            dfg.add_count(self.pattern_list[-1].get_activity_name(),
                          self.pattern_list[0].get_activity_name())

        for pattern in self.pattern_list:
            if recursive:
                pattern.expand_dfg(dfg.nodes[pattern.get_activity_name()], dfg)
            else:
                dfg.add_pattern(pattern.get_activity_name(), pattern)

    def fold_dfg(self, dfg: DirectlyFollowsGraph):
        super().fold_dfg(dfg)
        for activity in self.special_noise_set:
            if activity in dfg.nodes:
                dfg.remove_node(activity)

    def _generate_activity_name(self) -> str:
        activity_name = '[' + ','.join(p.get_activity_name()
                                       for p in self.pattern_list) +  ']'
        if self.special_noise_set:
            activity_name += '~{%s}' % ','.join(
                    sorted(self.special_noise_set))
        return activity_name

    def get_nr_of_subpatterns(self) -> int:
        return len(self.pattern_list)

    def get_subpatterns(self) -> List[Pattern]:
        return self.pattern_list

    def get_start_subpatterns(self) -> List['Pattern']:
        return [self.pattern_list[0]]

    def get_end_subpatterns(self) -> List['Pattern']:
        return [self.pattern_list[-1]]

    def get_encoded_length_in_code_table(
            self, available_activities: Set[str]) -> Tuple[float,Set[str]]:
        code_length = log2(len(available_activities))
        #types of the subpatterns including singleton
        code_length += len(self.pattern_list) * log2(NR_OF_PATTERN_TYPES_WITH_SINGLETON)
        for pattern in self.pattern_list:
            code_length_of_subpattern, available_activities = \
                pattern.get_encoded_length_in_code_table(
                    available_activities)
            code_length += code_length_of_subpattern
        #special noise set or not
        #code_length += 1
        if self.special_noise_set:
            #nr of special noise activities
            code_length += log2(len(available_activities))
            code_length += mdl_utils.log2binom(len(available_activities),
                                               len(self.special_noise_set))
        return code_length, available_activities

    def for_covering(self, trace, last_covered_activity: str):
        return CoveringSequence(self, trace, last_covered_activity)

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str):
        nr_of_nodes = 0
        last_pattern_id = None
        for pattern in self.pattern_list:
            pattern_id = base_id + '.' + str(nr_of_nodes)
            graph.add_node(pattern.create_node_for_nested_graph(
                    pattern_id, parent_id=base_id))
            pattern.add_subpatterns_to_nested_graph(graph, pattern_id)
            if nr_of_nodes > 0:
                graph.add_edge(NestedGraph.Edge(
                        last_pattern_id + '->' + pattern_id,
                        last_pattern_id, pattern_id))
            nr_of_nodes += 1
            last_pattern_id = pattern_id

    def _without_degeneration(self) -> Tuple[Pattern, bool]:
        """ a sequence is degenerated if it consists of only one element
        """
        if self.get_nr_of_subpatterns() == 1:
            return self.get_subpatterns()[0].without_degeneration()[0], True
        else:
            result_list = [p.without_degeneration() for p in self.pattern_list]
            changed = any(result[1] for result in result_list)
            if changed:
                self.pattern_list = [result[0] for result in result_list]
            return self, changed

    def _merge_subpatterns(self):
        new_pattern_list = []
        changed = False
        for subpattern in self.get_subpatterns():
            if subpattern.merge_subpatterns():
                changed = True
            if isinstance(subpattern, Sequence) and \
            self.special_noise_set == subpattern.special_noise_set:
                new_pattern_list.extend(subpattern.get_subpatterns())
                changed = True
            else:
                new_pattern_list.append(subpattern)
        self.pattern_list = new_pattern_list
        return changed

    def _remove_activity(self, activity: str):
        patterns_for_removal = []
        changed = False
        for pattern in self.pattern_list:
            try:
                if pattern.remove_activity(activity):
                    changed = True
            except ValueError:
                patterns_for_removal.append(pattern)
        for pattern in patterns_for_removal:
            self.pattern_list.remove(pattern)
        if self.get_nr_of_subpatterns() == 0:
            raise ValueError('Sequence must not be empty')
        return changed or patterns_for_removal

    def add_to_petri_net(self, petri_net: DataPetriNet) -> Tuple[Place,Place]:
        last_pattern = self.pattern_list[0]
        last_pre_place, last_post_place = last_pattern.add_to_petri_net(petri_net)
        pre_place = last_pre_place
        for current_pattern in self.pattern_list[1:]:
            transition = petri_net.add_transition(Transition(
                    last_pattern.get_activity_name() + '->' +
                    current_pattern.get_activity_name(), visible=False))
            current_pre_place, current_post_place = \
                current_pattern.add_to_petri_net(petri_net)
            petri_net.add_connection(last_post_place, transition,
                                     current_pre_place)
            last_post_place = current_post_place
            last_pre_place = current_pre_place
        return pre_place, last_post_place

    def _copy(self) -> 'Pattern':
        return Sequence(
                [subpattern.copy() for subpattern in self.get_subpatterns()],
                special_noise_set=set(self.special_noise_set))

    def _replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        self.pattern_list = [subpattern.replace_singleton(activity, pattern)
                             for subpattern in self.pattern_list]
        return self

    def _replace_direct_subpattern(self, subpattern: 'Pattern',
                                   replacement: 'Pattern'):
        self.pattern_list[self.pattern_list.index(subpattern)] = replacement

    def get_nr_of_forbidden_edges_in_pattern_dfg(
            self, pattern_dfg: DirectlyFollowsGraph) -> int:
        return 0

    def _start_activities(self) -> Set[str]:
        return self.pattern_list[0].start_activities()

    def _end_activities(self) -> Set[str]:
        return self.pattern_list[-1].end_activities()

    def generate_activities(self, random: Random = None) -> List[str]:
        activities = []
        for subpattern in self.get_subpatterns():
            activities.extend(subpattern.generate_activities(random=random))
        return activities

    def get_activity_set(self) -> Set[str]:
        activity_set = super().get_activity_set()
        if self.special_noise_set:
            activity_set.update(self.special_noise_set)
        return activity_set

    @staticmethod
    def from_activity_list(activity_list: List[str]):
        return Sequence([Singleton(a) for a in activity_list])