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
from prolothar_common.models.dfg.node import Node

from prolothar_common.models.data_petri_net import DataPetriNet
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_common.models.nested_graph import NestedGraph

from typing import Tuple, Set, List

from random import Random

class Singleton(Pattern):
    def __init__(self, activity: str): ...

    def expand_dfg(self, node: Node, dfg: DirectlyFollowsGraph,
                   recursive: bool = True): ...

    def fold_dfg(self, dfg: DirectlyFollowsGraph): ...

    def contains_activity(self, activity: str) -> bool: ...

    def get_activity_name(self) -> str: ...

    def _generate_activity_name(self) -> str: ...

    def get_activity_set(self) -> Set[str]: ...

    def get_nr_of_subpatterns(self) -> int: ...

    def get_subpatterns(self) -> List[Pattern]: ...

    def get_start_subpatterns(self) -> List[Pattern]: ...

    def get_end_subpatterns(self) -> List[Pattern]: ...

    def get_encoded_length_in_code_table(self, available_activities: Set[str]) -> Tuple[float,Set[str]]: ...

    def for_covering(self, trace, last_covered_activity: str): ...

    def add_subpatterns_to_nested_graph(self, graph: NestedGraph, base_id: str): ...

    def _without_degeneration(self): ...

    def without_degeneration(self): ...

    def _merge_subpatterns(self): ...

    def _remove_activity(self, activity: str): ...

    def _copy(self) -> Pattern: ...

    def add_to_petri_net(self, petri_net: DataPetriNet): ...

    def _replace_singleton(self, activity: str, pattern: Pattern) -> Pattern: ...

    def _replace_direct_subpattern(self, subpattern: Pattern, replacement: Pattern): ...

    def get_nr_of_forbidden_edges_in_pattern_dfg(self, pattern_dfg: DirectlyFollowsGraph) -> int: ...

    def _start_activities(self) -> Set[str]: ...

    def _end_activities(self) -> Set[str]: ...

    def generate_activities(self, random: Random = None) -> List[str]: ...