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
from collections import deque

from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_common.models.dfg.node import Node

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import NR_OF_PATTERN_TYPES_WITH_SINGLETON
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Transition, Place

from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_parallel import CoveringParallel

from math import log2

from random import Random

class Parallel(Pattern):
    def __init__(self, branches: List[Pattern]):
        super().__init__()
        self.branches = branches
        #sort options such that comparisons are order invariant
        self.branches.sort(key=Pattern.get_activity_name)

    def expand_dfg(self, node: Node, dfg, recursive: bool = True):
        if not recursive:
            raise ValueError('parallels can only be expanded if recursive')

        preceeding_activities = dfg.get_preceeding_activities(node.activity)
        following_activities = dfg.get_following_activities(node.activity)

        dfg.remove_node(node.activity)
        for pattern in self.branches:
            dfg.add_node(pattern.get_activity_name())
            #handle ingoing edges
            for preceeding_activity in preceeding_activities:
                if node.activity != preceeding_activity:
                    dfg.add_count(preceeding_activity,
                                  pattern.get_activity_name())
            #handle outgoing edges
            for following_activity in following_activities:
                if node.activity != following_activity:
                    dfg.add_count(pattern.get_activity_name(),
                                  following_activity)

        for pattern in self.branches:
            pattern.expand_dfg(dfg.nodes[pattern.get_activity_name()], dfg)

        #connect all subpatterns
        for i,subpattern_i in enumerate(self.branches):
            for j,subpattern_j in enumerate(self.branches):
                if i != j:
                    self.__connect_expanded_branches(
                            dfg, subpattern_i, subpattern_j)

    def __connect_expanded_branches(self, dfg: DirectlyFollowsGraph,
                                    branch_i: Pattern, branch_j: Pattern):
        for activity_i in branch_i.get_activity_set():
            for activity_j in branch_j.get_activity_set():
                dfg.add_count(activity_i, activity_j)
                dfg.add_count(activity_j, activity_i)

    def fold_dfg(self, dfg: DirectlyFollowsGraph):
        super().fold_dfg(dfg)
        dfg.remove_edge((self.get_activity_name(),
                         self.get_activity_name()))

    def _generate_activity_name(self) -> str:
        return '(' + '||'.join(p.get_activity_name() for p in self.branches) + ')'

    def get_nr_of_subpatterns(self) -> int:
        return len(self.branches)

    def get_subpatterns(self) -> List[Pattern]:
        return self.branches

    def get_start_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def get_end_subpatterns(self) -> List['Pattern']:
        return self.get_subpatterns()

    def get_encoded_length_in_code_table(
            self, available_activities: Set[str]) -> Tuple[float,Set[str]]:
        code_length = log2(len(available_activities))
        #types of the subpatterns including singleton
        code_length += len(self.branches) * log2(NR_OF_PATTERN_TYPES_WITH_SINGLETON)
        for pattern in self.branches:
            code_Length_of_branch, available_activities = \
                pattern.get_encoded_length_in_code_table(available_activities)
            code_length += code_Length_of_branch
        return code_length, available_activities

    def for_covering(self, trace, last_covered_activity: str):
        return CoveringParallel(self, trace, last_covered_activity)

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str):
        nr_of_nodes = 0
        for pattern in self.branches:
            pattern_id = base_id + '.' + str(nr_of_nodes)
            graph.add_node(pattern.create_node_for_nested_graph(
                    pattern_id, parent_id=base_id))
            pattern.add_subpatterns_to_nested_graph(graph, pattern_id)
            nr_of_nodes += 1

    def _without_degeneration(self) -> Tuple[Pattern, bool]:
        """ a parallel pattern is degenerated if it consists of only one branch
        """
        if self.get_nr_of_subpatterns() == 1:
            return self.branches[0].without_degeneration()[0], True
        else:
            result_list = [p.without_degeneration() for p in self.branches]
            changed = any(result[1] for result in result_list)
            if changed:
                self.branches = [result[0] for result in result_list]
            return self, changed

    def _merge_subpatterns(self):
        new_branches = []
        changed = False
        for branch in self.get_subpatterns():
            if branch.merge_subpatterns():
                changed = True
            if isinstance(branch, Parallel):
                new_branches.extend(branch.get_subpatterns())
                changed = True
            else:
                new_branches.append(branch)
        self.branches = new_branches
        return changed

    def _remove_activity(self, activity: str):
        patterns_for_removal = []
        changed = False
        for pattern in self.branches:
            if pattern.is_singleton() and pattern.contains_activity(activity):
                patterns_for_removal.append(pattern)
            elif pattern.remove_activity(activity):
                changed = True
        for pattern in patterns_for_removal:
            self.branches.remove(pattern)
        if self.get_nr_of_subpatterns() == 0:
            raise ValueError('Parallel must not be empty')
        return changed or patterns_for_removal

    def _copy(self) -> 'Pattern':
        return Parallel([subpattern.copy() for subpattern in self.get_subpatterns()])

    def add_to_petri_net(self, petri_net: DataPetriNet) -> Tuple[Place,Place]:
        activity_name = self.get_activity_name()
        pre_place = petri_net.add_place(Place.with_empty_label(
                '__pre__' + activity_name))
        post_place = petri_net.add_place(Place.with_empty_label(
                '__post__' + activity_name))
        pre_transition = petri_net.add_transition(Transition(
                '__pre__' + activity_name, visible=False))
        post_transition = petri_net.add_transition(Transition(
                '__post__' + activity_name, visible=False))

        for branch in self.get_subpatterns():
            branch_pre_place, branch_post_place = branch.add_to_petri_net(petri_net)
            petri_net.add_connection(pre_place, pre_transition, branch_pre_place)
            petri_net.add_connection(branch_post_place, post_transition, post_place)

        return pre_place, post_place

    def _replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        self.branches = [subpattern.replace_singleton(activity, pattern)
                         for subpattern in self.branches]
        return self

    def _replace_direct_subpattern(self, subpattern: 'Pattern',
                                   replacement: 'Pattern'):
        self.branches[self.branches.index(subpattern)] = replacement

    def get_nr_of_forbidden_edges_in_pattern_dfg(
            self, pattern_dfg: DirectlyFollowsGraph) -> int:
        return 0

    def _start_activities(self) -> Set[str]:
        start_activities = set()
        for branch in self.branches:
            start_activities.update(branch.start_activities())
        return start_activities

    def _end_activities(self) -> Set[str]:
        end_activities = set()
        for branch in self.branches:
            end_activities.update(branch.end_activities())
        return end_activities

    def generate_activities(self, random: Random = None) -> List[str]:
        if random is None:
            random = Random()
        branches = [deque(branch.generate_activities(random))
                    for branch in self.branches]
        activities = []
        while branches:
            branch = random.choice(branches)
            if branch:
                activities.append(branch.popleft())
            else:
                branches.remove(branch)
        return activities

    @staticmethod
    def from_activity_list(activity_list: List[str]):
        return Parallel([Singleton(a) for a in activity_list])