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
from typing import Set, Union

def find_one_step_choices_in_dfg(dfg: DirectlyFollowsGraph) -> Set[Choice]:
    """finds choices where each branch consists of one activity
    """
    root_candidates = _generate_root_candidates(dfg)

    choices = _find_choices_from_root_candidates(root_candidates, dfg)

    choices = choices.union(_find_choices_from_sources(dfg))

    if isinstance(dfg, PatternDfg):
        for choice in choices:
            for i, option in enumerate(choice.options):
                choice.options[i] = dfg.nodes[option.activity].pattern

    return choices

def find_one_step_choice_from_branch_candidate_node(
        dfg: DirectlyFollowsGraph, node: Node) -> Union[Choice, None]:
    """returns a choice pattern if the given node is branch of a
    perfectly matching choice pattern. otherwise returns None
    """
    if len(node.ingoing_edges) == 1:
        choices = _find_choices_from_root_candidates(
                set([node.ingoing_edges[0].start]), dfg)
        if choices:
            choice = next(iter(choices))
            if isinstance(dfg, PatternDfg):
                for i, option in enumerate(choice.options):
                    choice.options[i] = dfg.nodes[option.activity].pattern
            return choice
    return None

def _generate_root_candidates(dfg: DirectlyFollowsGraph) -> Set[Node]:
    root_candidate = set()
    for node in dfg.nodes.values():
        if len(node.edges) >= 2:
            root_candidate.add(node)
    return root_candidate

def _find_choices_from_root_candidates(root_candidate_set: Set[Node],
                                       dfg: DirectlyFollowsGraph):
    choices = set()
    for root_candidate in root_candidate_set:
        _create_choice_from_root(root_candidate, choices, dfg)
    return choices

def _create_choice_from_root(root: Node, choices: Set[Choice],
                             dfg: DirectlyFollowsGraph):
    """all options must have the same set of predecessor and ancestors"""

    end_dict = {}

    for edge in root.edges:
        option_preceding_activities = frozenset(dfg.get_preceeding_activities(
            edge.end.activity))
        option_following_activities = frozenset(dfg.get_following_activities(
            edge.end.activity))

        dict_key = (option_preceding_activities, option_following_activities)
        if dict_key not in end_dict:
            end_dict[dict_key] = []
        end_dict[dict_key].append(edge.end.activity)

    _create_choices_from_end_dict(end_dict, choices)

def _find_choices_from_sources(dfg: DirectlyFollowsGraph):
    choices = set()
    end_dict = {}
    for node in dfg.get_source_nodes():
        following_activities = frozenset(
                dfg.get_following_activities(node.activity))
        if not following_activities in end_dict:
            end_dict[following_activities] = []
        end_dict[following_activities].append(node.activity)
    _create_choices_from_end_dict(end_dict, choices)
    return choices

def _create_choices_from_end_dict(end_dict, choices):
    for choice_nodes in end_dict.values():
        if len(choice_nodes) >= 2:
            choices.add(Choice([Singleton(a) for a in choice_nodes]))




