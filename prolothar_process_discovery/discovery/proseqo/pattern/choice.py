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

from typing import Set, List, Tuple

from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_common.models.dfg.node import Node

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import NR_OF_PATTERN_TYPES_WITH_SINGLETON
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_choice import CoveringChoice
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Transition, Place

from math import log2
from random import Random

class Choice(Pattern):
    """a pattern where the subpatterns are a list of exclusive choices, e.g.
    (A|B|C) = A XOR B XOR C
    """

    def __init__(self, options: List[Pattern]):
        super().__init__()
        self.options = options
        #sort options such that comparisons are order invariant
        self.options.sort(key=lambda option: option.get_activity_name())

    def expand_dfg(self, node: Node, dfg: DirectlyFollowsGraph,
                   recursive: bool = True):

        for option in self.options:
            dfg.add_node(option.get_activity_name())

        need_to_handle_selfloop = self._expand_handle_ingoing_edges(node, dfg)

        self._expand_handle_outgoing_edges(node, dfg)

        if need_to_handle_selfloop:
            for option_a in self.options:
                for option_b in self.options:
                    dfg.add_count(option_a.get_activity_name(),
                                  option_b.get_activity_name())

        dfg.remove_node(node.activity)
        for option in self.options:
            if recursive:
                option.expand_dfg(dfg.nodes[option.get_activity_name()], dfg)
            else:
                dfg.add_pattern(option.get_activity_name(), option)

    def _expand_handle_ingoing_edges(self, node: Node,
                                     dfg: DirectlyFollowsGraph) -> bool:
        need_to_handle_selfloop = False
        for preceeding_activity in dfg.get_preceeding_activities(node.activity):
            #handle self-loops. otherwise removed pattern would be added again
            if node.activity != preceeding_activity:
                for option in self.options:
                    dfg.add_count(preceeding_activity, option.get_activity_name())
            else:
                need_to_handle_selfloop = True
        return need_to_handle_selfloop

    def _expand_handle_outgoing_edges(self, node: Node, dfg: DirectlyFollowsGraph):
        for following_activity in dfg.get_following_activities(node.activity):
            if node.activity != following_activity:
                for option in self.options:
                    dfg.add_count(option.get_activity_name(), following_activity)

    def _generate_activity_name(self) -> str:
        return '(' + '|'.join(o.get_activity_name() for o in self.options) + ')'

    def get_nr_of_subpatterns(self) -> int:
        return len(self.options)

    def get_start_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def get_end_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def get_subpatterns(self) -> List[Pattern]:
        return self.options

    def get_encoded_length_in_code_table(
            self, available_activities: Set[str]) -> Tuple[float,Set[str]]:
        code_length = log2(len(available_activities))
        #types of the subpatterns including singleton
        code_length += len(self.options) * log2(NR_OF_PATTERN_TYPES_WITH_SINGLETON)
        for option in self.options:
            code_length_of_option, available_activities = \
                option.get_encoded_length_in_code_table(
                        available_activities)
            code_length += code_length_of_option
        return code_length, available_activities

    def for_covering(self, trace, last_covered_activity: str):
        return CoveringChoice(self, trace, last_covered_activity)

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str):
        for i, option in enumerate(self.options):
            option_id = '%s.%d' % (base_id, i)
            graph.add_node(option.create_node_for_nested_graph(
                        option_id, parent_id=base_id))
            option.add_subpatterns_to_nested_graph(graph, option_id)

    def _without_degeneration(self) -> Tuple[Pattern, bool]:
        """ a choice is degenerated if there is only one pattern to choose
        """
        if self.get_nr_of_subpatterns() == 1:
            return self.get_subpatterns()[0].without_degeneration()[0], True
        else:
            recursive_result_list = [option.without_degeneration()
                                     for option in self.options]
            changed = any(result[1] for result in recursive_result_list)
            if changed:
                self.options = [result[0] for result in recursive_result_list]
                self.options.sort(key=lambda option: option.get_activity_name())

            if self._one_option_is_optional():
                self.options = [
                    option.get_subpattern() if option.is_optional() else option
                    for option in self.options]
                return Optional(self), True
            else:
                return self, changed

    def _one_option_is_optional(self):
        for option in self.options:
            if option.is_optional():
                return True
        return False

    def _merge_subpatterns(self):
        new_options = []
        changed = False
        for option in self.options:
            if option.merge_subpatterns():
                changed = True
            if isinstance(option, Choice):
                new_options.extend(option.get_subpatterns())
                changed = True
            else:
                new_options.append(option)
        self.options = new_options
        if changed:
            self.options.sort(key=lambda option: option.get_activity_name())
        return changed

    def _remove_activity(self, activity: str) -> bool:
        patterns_for_removal = []
        changed = False
        for pattern in self.options:
            try:
                if pattern.remove_activity(activity):
                    changed = True
            except ValueError:
                patterns_for_removal.append(pattern)
        for pattern in patterns_for_removal:
            self.options.remove(pattern)
        if not self.options:
            raise ValueError('Choice must not be empty')
        return changed or patterns_for_removal

    def _copy(self) -> 'Pattern':
        return Choice([subpattern.copy() for subpattern in self.get_subpatterns()])

    def add_to_petri_net(self, petri_net: DataPetriNet) -> Tuple[Place,Place]:
        activity_name = self.get_activity_name()
        pre_place = petri_net.add_place(Place.with_empty_label(
                '__pre__' + activity_name))
        post_place = petri_net.add_place(Place.with_empty_label(
                '__post__' + activity_name))

        for i,option in enumerate(self.get_subpatterns()):
            pre_transition = petri_net.add_transition(Transition(
                    '__pre%d__%s' % (i,activity_name), visible=False))
            post_transition = petri_net.add_transition(Transition(
                    '__post%d__%s' % (i,activity_name), visible=False))
            option_pre_place, option_post_place = option.add_to_petri_net(petri_net)
            petri_net.add_connection(pre_place, pre_transition, option_pre_place)
            petri_net.add_connection(option_post_place, post_transition, post_place)

        return pre_place, post_place

    def _replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        self.options = [subpattern.replace_singleton(activity, pattern)
                        for subpattern in self.options]
        return self

    def _replace_direct_subpattern(self, subpattern: 'Pattern',
                                   replacement: 'Pattern'):
        self.options[self.options.index(subpattern)] = replacement

    def get_nr_of_forbidden_edges_in_pattern_dfg(self, pattern_dfg) -> int:
        return 0

    def _start_activities(self) -> Set[str]:
        start_activities = set()
        for option in self.options:
            start_activities.update(option.start_activities())
        return start_activities

    def _end_activities(self) -> Set[str]:
        end_activities = set()
        for option in self.options:
            end_activities.update(option.end_activities())
        return end_activities

    def generate_activities(self, random: Random = None) -> List[str]:
        if random is None:
            random = Random()
        return random.choice(self.options).generate_activities(random)
