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
from prolothar_common.models.directly_follows_graph import Node
from prolothar_common.models.data_petri_net import DataPetriNet, Transition, Place
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_singleton import CoveringSingleton
from prolothar_common.models.nested_graph import NestedGraph

from typing import Tuple, Set, List
from math import log2

from random import Random

class Singleton(Pattern):
    def __init__(self, activity: str):
        super().__init__()
        self.activity = activity

    def expand_dfg(self, node: Node, dfg: DirectlyFollowsGraph,
                   recursive: bool = True):
        #singleton is already maximal expanded
        pass

    def fold_dfg(self, dfg: DirectlyFollowsGraph):
        #singleton cannot folder more than one node...
        pass

    def contains_activity(self, activity: str):
        return self.activity == activity

    def get_activity_name(self) -> str:
        return self.activity

    def _generate_activity_name(self) -> str:
        return self.activity

    def get_activity_set(self) -> Set[str]:
        return set([self.activity])

    def get_nr_of_subpatterns(self) -> int:
        return 0

    def get_subpatterns(self) -> List[Pattern]:
        return []


    def get_start_subpatterns(self) -> List['Pattern']:
        return []

    def get_end_subpatterns(self) -> List['Pattern']:
        return []

    def get_encoded_length_in_code_table(
            self, available_activities: Set[str]) -> Tuple[float,Set[str]]:
        code_length = log2(len(available_activities))
        return code_length, available_activities

    def for_covering(self, trace, last_covered_activity: str):
        return CoveringSingleton(self, trace, last_covered_activity)

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str):
        pass

    def _without_degeneration(self):
        """ a singleton can never be degenerated
        """
        return self, False

    def without_degeneration(self):
        """ a singleton can never be degenerated
        """
        return self, False

    def _merge_subpatterns(self):
        # a singleton has no subpatterns to merge
        return False

    def _remove_activity(self, activity: str):
        if self.activity == activity:
            raise ValueError('empty singletons are not allowed')
        return False

    def _copy(self) -> 'Pattern':
        return Singleton(self.activity)

    def add_to_petri_net(self, petri_net: DataPetriNet):
        activity_name = self.get_activity_name()
        transition = petri_net.add_transition(Transition(activity_name))
        pre_place = petri_net.add_place(Place.with_empty_label(
                '__pre__' + activity_name))
        post_place = petri_net.add_place(Place.with_empty_label(
                '__post__' + activity_name))
        petri_net.add_connection(pre_place, transition, post_place)
        return pre_place, post_place

    def _replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        if activity == self.activity:
            return pattern
        else:
            return self

    def _replace_direct_subpattern(self, subpattern: 'Pattern',
                                   replacement: 'Pattern'):
        raise ValueError()

    def get_nr_of_forbidden_edges_in_pattern_dfg(
            self, pattern_dfg: DirectlyFollowsGraph) -> int:
        return 0

    def _start_activities(self) -> Set[str]:
        return set([self.activity])

    def _end_activities(self) -> Set[str]:
        return set([self.activity])

    def generate_activities(self, random: Random = None) -> List[str]:
        return [self.activity]