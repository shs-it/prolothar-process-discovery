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
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from typing import Set, List

from itertools import combinations

def find_binary_choice_candidates_in_dfg(dfg: DirectlyFollowsGraph) -> Set[Choice]:
    """finds possible choices: for each node pairs of following and pairs of
    preceding activities will be returned as choice candidates
    """
    choices = set()
    for node in dfg.get_nodes():
        choices = choices.union(_create_choice_canidates_from_node(node))
    if isinstance(dfg, PatternDfg):
        for choice in choices:
            for i, option in enumerate(choice.options):
                choice.options[i] = dfg.nodes[option.activity].pattern
    return choices

def _create_choice_canidates_from_node(node: Node) -> Set[Choice]:
    choices = _create_choices_from_activities([
            edge.start.activity for edge in node.ingoing_edges])
    choices = choices.union(_create_choices_from_activities([
            edge.end.activity for edge in node.edges]))
    return choices

def _create_choices_from_activities(activities: List[str]) -> Set[Choice]:
    choices = set()
    if len(activities) >= 2:
        for activity_a, activity_b in combinations(activities, 2):
            choices.add(Choice([Singleton(activity_a),
                                Singleton(activity_b)]))
    return choices