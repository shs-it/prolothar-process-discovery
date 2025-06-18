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
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_blob import CoveringBlob

from prolothar_common.models.dfg.node import Node

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Transition, Place
from prolothar_common.models.nested_graph import NestedGraph
from random import Random

from math import log2
from prolothar_common import mdl_utils

class Blob(Pattern):
    """a pattern where the activities are all possible and repetitions are also
    allowed.
    """

    def __init__(self, activities: Set[str]):
        """
        Args:
            activities:
                set of activities in the blob
            self_loops:
                If True, activities can occur twice in a row, otherwise
                another activity must occur before an activity may be repeated
        """
        super().__init__()
        self.__activities = activities

    def _generate_activity_name(self) -> str:
        return '{' + ','.join(sorted(self.__activities)) + '}'

    def contains_activity(self, activity: str) -> str:
        return activity in self.__activities

    def for_covering(self, trace, last_covered_activity: str):
        return CoveringBlob(self, trace, last_covered_activity)

    def get_activity_set(self) -> Set[str]:
        return self.__activities

    def expand_dfg(self, node: Node, dfg: DirectlyFollowsGraph,
                   recursive: bool = True):
        for preceding_activity in dfg.get_preceeding_activities(
                self.get_activity_name()):
            for activity in self.__activities:
                dfg.add_count(preceding_activity, activity)

        for following_activity in dfg.get_following_activities(
                self.get_activity_name()):
            for activity in self.__activities:
                dfg.add_count(activity, following_activity)

        for activity in self.__activities:
            for other_activity in self.__activities:
                if activity != other_activity:
                    dfg.add_count(activity, other_activity)

        dfg.remove_node(node.activity)

    def fold_dfg(self, dfg: DirectlyFollowsGraph):
        super().fold_dfg(dfg)
        dfg.remove_edge((self.get_activity_name(),
                         self.get_activity_name()))

    def get_start_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def get_end_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def get_subpatterns(self) -> List[Pattern]:
        return [Singleton(a) for a in self.__activities]

    def get_nr_of_subpatterns(self) -> int:
        return len(self.__activities)

    def _copy(self) -> Pattern:
        return Blob(set(self.__activities))

    def _start_activities(self) -> Set[str]:
        return self.__activities

    def _end_activities(self) -> Set[str]:
        return self.__activities

    def _merge_subpatterns(self):
        #blob has only singleton
        return self

    def _remove_activity(self, activity: str) -> bool:
        try:
            self.__activities.remove(activity)
            if not self.__activities:
                raise ValueError('blob is empty after deletion')
            return True
        except KeyError:
            return False

    def get_nr_of_forbidden_edges_in_pattern_dfg(self, pattern_dfg) -> int:
        return 0

    def _replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        if activity in self.__activities and not pattern.is_singleton():
            raise NotImplementedError(
                    'not allowed on blob. blob only contains singletons')

    def _replace_direct_subpattern(self, subpattern: 'Pattern',
                                   replacement: 'Pattern'):
        raise ValueError('Blob does not contain subpatterns')

    def add_to_petri_net(self, petri_net: DataPetriNet) -> Tuple[Place,Place]:
        activity_name = self.get_activity_name()
        pre_place = petri_net.add_place(Place.with_empty_label(
                '__pre__' + activity_name))
        post_place = petri_net.add_place(Place.with_empty_label(
                '__post__' + activity_name))

        activty_place_dict = {}
        activty_transition_dict = {}
        for activity in self.__activities:
            transition = petri_net.add_transition(
                    Transition(activity, activity))
            place = petri_net.add_place(Place.with_empty_label(
                '__post__' + activity))
            end_transition = petri_net.add_transition(Transition(
                    '__end__' + activity, '', visible=False))

            petri_net.add_connection(pre_place, transition, place)
            petri_net.add_connection(place, end_transition, post_place)
            activty_place_dict[activity] = place
            activty_transition_dict[activity] = transition

        for activity in self.__activities:
            for other_activity in self.__activities:
                if activity != other_activity:
                    transition = petri_net.add_transition(
                            Transition(activity + '__' + other_activity, other_activity))
                    petri_net.add_connection(
                            activty_place_dict[activity],
                            transition,
                            activty_place_dict[other_activity])

        return pre_place, post_place

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str):
        activities = sorted(self.__activities)
        for i,activity in enumerate(activities):
            node_id = base_id + '.' + str(i)
            graph.add_node(Singleton(activity).create_node_for_nested_graph(
                    node_id, base_id))
            for j,other_activity in enumerate(activities):
                if i != j:
                    other_node_id = base_id + '.' + str(j)
                    graph.add_edge(NestedGraph.Edge(
                        node_id + '->' + other_node_id,
                        node_id, other_node_id))

    def generate_activities(self, random: Random = None) -> List[str]:
        if random is None:
            random = Random()
        generated_activities = [random.choice(list(self.__activities))]
        while random.uniform(0,1) > 0.5:
            generated_activities.append(random.choice(
                list(self.__activities.difference([generated_activities[-1]]))))
        return generated_activities

    def _without_degeneration(self) -> Tuple[Pattern, bool]:
        #a blob cannot be degenerated because there are no complex subpatterns
        return self, False

    def get_encoded_length_in_code_table(
            self, available_activities: Set[str]) -> Tuple[float,Set[str]]:
        code_length = log2(len(available_activities))
        code_length += mdl_utils.log2binom(len(available_activities),
                                           len(self.__activities))
        return code_length, available_activities
