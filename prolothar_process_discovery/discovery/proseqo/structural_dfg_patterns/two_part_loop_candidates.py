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

from typing import List

from prolothar_process_discovery.discovery.proseqo.pattern.loop import Loop
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.dfg.node import Node

def find_two_part_loop_candidates_in_dfg(dfg: DirectlyFollowsGraph) -> List[Loop]:
    """finds pattern candidates of the form "[a,b?]+"
    """

    if not isinstance(dfg, PatternDfg):
        dfg = PatternDfg.create_from_dfg(dfg)

    start_candidates = _find_nodes_with_self_loops(dfg)
    loop_candidates = _create_loop_candidates(start_candidates, dfg)

    return [loop.without_degeneration()[0] for loop in loop_candidates]

def _find_nodes_with_self_loops(dfg: DirectlyFollowsGraph):
    return [node for node in dfg.get_nodes()
            if node.is_followed_by(node.activity)]

def _create_loop_candidates(start_candidates: List[Node],
                            dfg: DirectlyFollowsGraph):
    loop_candidates = []
    for start_candidate in start_candidates:
        loop_candidates.extend(_create_loop_candidates_from_start_candidate(
                start_candidate, dfg))
    return loop_candidates

def _create_loop_candidates_from_start_candidate(
                start_candidate: Node, dfg: DirectlyFollowsGraph) -> List[Loop]:
    loop_candidates = []
    for following_activity in dfg.get_following_activities(start_candidate.activity):
        if following_activity != start_candidate.activity:
            if dfg.nodes[following_activity].is_followed_by(start_candidate.activity):
                loop_candidates.append(Loop(Sequence([
                        start_candidate.pattern,
                        Optional(dfg.nodes[following_activity].pattern)
                ])))
    return loop_candidates