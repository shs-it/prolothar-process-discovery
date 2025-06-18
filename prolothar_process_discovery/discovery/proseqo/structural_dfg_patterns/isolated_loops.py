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
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern.loop import Loop
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import return_induced_sequence_if_existing

from typing import List

def find_isolated_loops_in_dfg(
        dfg: DirectlyFollowsGraph,
        find_induced_sequences: bool = False) -> List[Loop]:
    """finds isolated sequences with loop, i.e. sequences of the following form:
    A=>[B1,...,BK]=>C=>A,
    with A having the only ingoing connections from other nodes, [B1,...,BK]
    is a chain of nodes with no other connections, and C is the only having
    outgoing edges to other nodes. this method finds loops of length >= 1, e.g.
    A => A, A => B => A, ...
    """

    loops = _construct_loops(dfg.get_nodes(), dfg)

    if isinstance(dfg, PatternDfg):
        for loop in loops:
            if loop.subpattern.is_singleton():
                loop.subpattern = dfg.nodes[loop.subpattern.activity].pattern
            else:
                loop.subpattern.pattern_list = [
                    dfg.nodes[p.activity].pattern
                    for p in loop.subpattern.pattern_list
                ]

    if find_induced_sequences:
        induced_loops = []
        for loop in loops:
            try:
                induced_loops.append(
                    return_induced_sequence_if_existing(loop, dfg))
            except KeyError:
                pass
            except ValueError:
                pass
        return induced_loops
    else:
        return loops

def _construct_loops(start_candidates: List[Node],
                     dfg: DirectlyFollowsGraph) -> List[Loop]:
    """tries to find loops from the start candidate list"""
    loops = []
    for start_candidate in start_candidates:
        _add_loop_from_start_candidate_if_possible(
                start_candidate, dfg, loops)
    return loops

def _add_loop_from_start_candidate_if_possible(
        start_candidate: Node, dfg: DirectlyFollowsGraph,
        loops: List[Loop]):
    """adds a loop of length "loop_length" to "loops" starting from
    "start_candidate" if there are no disturbing connections"""
    activity_sequence = [start_candidate.activity]
    current_node = start_candidate
    #the number of nodes is an upper bound of the loop length and prevents
    #the loop from running forever if there is a subloop
    for _ in range(dfg.get_nr_of_nodes()):
        #test if we are at the start activity again => loop found
        if start_candidate.activity in dfg.get_following_activities(current_node.activity):
            if len(activity_sequence) == 1:
                loops.append(Loop(Singleton(activity_sequence[0])))
            else:
                loops.append(Loop(Sequence.from_activity_list(activity_sequence)))
            break
        #no sequence => break

        if not len(current_node.edges) == 1:
            break

        current_node = current_node.edges[0].end

        #no sequence => break
        if not len(current_node.ingoing_edges) == 1:
            break

        activity_sequence.append(current_node.activity)




