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
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_common.models.dfg.node import Node

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import NR_OF_PATTERN_TYPES_WITH_SINGLETON
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_inclusive_choice import CoveringInclusiveChoice
from prolothar_common.models.nested_graph import NestedGraph
from prolothar_common.models.data_petri_net import DataPetriNet, Transition, Place

from random import Random

class InclusiveChoice(Pattern):
    """a pattern where the subpatterns are a list of inclusive choices, e.g.
    (A,B,C) => A,B,C,AB,AC,BC,ABC,BA,CA,CB,CBA,ACB,BCA,BAC
    """

    def __init__(self, options: List[Pattern]):
        super().__init__()
        self.options = options
        #sort options such that comparisons are order invariant
        self.options.sort(key=lambda option: option.get_activity_name())

    def expand_dfg(self, node: Node, dfg: DirectlyFollowsGraph,
                   recursive: bool = True):
        preceeding_activities = dfg.get_preceeding_activities(node.activity)
        following_activities = dfg.get_following_activities(node.activity)

        dfg.remove_node(node.activity)
        for pattern in self.options:
            dfg.add_node(pattern.get_activity_name())
            #handle ingoing edges
            for preceeding_activity in preceeding_activities:
                dfg.add_count(preceeding_activity,
                              pattern.get_activity_name())
            #handle outgoing edges
            for following_activity in following_activities:
                dfg.add_count(pattern.get_activity_name(),
                              following_activity)

        #connect all subpatterns (we can go any order of them)
        for i,option_i in enumerate(self.options):
            for j,option_j in enumerate(self.options):
                if i != j:
                    dfg.add_count(option_i.get_activity_name(),
                                  option_j.get_activity_name())

        for pattern in self.options:
            pattern.expand_dfg(dfg.nodes[pattern.get_activity_name()], dfg)

    def fold_dfg(self, dfg: DirectlyFollowsGraph):
        super().fold_dfg(dfg)
        dfg.remove_edge((self.get_activity_name(),
                         self.get_activity_name()))

    def _generate_activity_name(self) -> str:
        return '(' + ','.join(o.get_activity_name() for o in self.options) + ')'

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
        return Choice.get_encoded_length_in_code_table(self, available_activities)

    def for_covering(self, trace, last_covered_activity: str):
        return CoveringInclusiveChoice(self, trace, last_covered_activity)

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str):
        Choice.add_subpatterns_to_nested_graph(self, graph, base_id)

    def _without_degeneration(self) -> Tuple[Pattern, bool]:
        return Choice._without_degeneration(self)

    def _merge_subpatterns(self):
        new_options = []
        changed = False
        for option in self.options:
            if option.merge_subpatterns():
                changed = True
            if isinstance(option, InclusiveChoice):
                new_options.extend(option.get_subpatterns())
                changed = True
            else:
                new_options.append(option)
        self.options = new_options
        if changed:
            self.options.sort(key=lambda option: option.get_activity_name())
        return changed

    def _remove_activity(self, activity: str) -> bool:
        return Choice._remove_activity(self, activity)

    def _copy(self) -> 'Pattern':
        return InclusiveChoice([subpattern.copy()
                                for subpattern in self.get_subpatterns()])

    def add_to_petri_net(self, petri_net: DataPetriNet) -> Tuple[Place,Place]:
        raise NotImplementedError()

    def _replace_singleton(self, activity: str, pattern: 'Pattern') -> 'Pattern':
        self.options = [subpattern.replace_singleton(activity, pattern)
                        for subpattern in self.options]
        return self

    def _replace_direct_subpattern(self, subpattern: 'Pattern',
                                   replacement: 'Pattern'):
        Choice._replace_direct_subpattern(self, subpattern, replacement)

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
        raise NotImplementedError()
