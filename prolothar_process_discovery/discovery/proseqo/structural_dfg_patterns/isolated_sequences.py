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
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence

from typing import Set, Union

def find_isolated_sequences_in_dfg(dfg: DirectlyFollowsGraph) -> Set[Sequence]:
    """finds isolated sequences, i.e. sequences of the following form:
    A=>[B1,...,BK]=>C,
    with A having the only ingoing connections from other nodes, [B1,...,BK]
    is a chain of nodes with no other connections, and C is the only having
    outgoing edges to other nodes"""
    start_candidates, part_candidates = \
        _find_sequence_nodes_candidates(dfg)

    sequences = _construct_sequences(start_candidates, part_candidates, dfg)

    return sequences

def find_isolated_sequence_from_candidate_node(
        dfg: DirectlyFollowsGraph, node: Node) -> Union[Sequence, None]:
    """returns a sequence pattern if the given node is part of a perfectly
    matching sequence. otherwise returns None"""
    start_candidates = set()
    part_candidates = set()
    _add_node_to_start_or_part_candidates(
                dfg, node, start_candidates, part_candidates)
    #and condition is to prevent endless loop when there is a cycle in the graph
    potential_start = node
    i = 0
    while len(potential_start.ingoing_edges) == 1 \
            and potential_start.ingoing_edges[0].start.activity not in part_candidates\
            and i <= dfg.get_nr_of_nodes():
        potential_start = potential_start.ingoing_edges[0].start
        _add_node_to_start_or_part_candidates(
                    dfg, potential_start, start_candidates, part_candidates)
        if potential_start.is_followed_by(potential_start.activity):
            break
        i += 1
    sequences = _construct_sequences(start_candidates, part_candidates, dfg)

    for sequence in sequences:
        for element in sequence.get_subpatterns():
            if element.get_activity_name() == node.activity:
                return sequence

    return None

def return_induced_sequence_if_existing(
        pattern: Pattern, dfg: DirectlyFollowsGraph) -> Union[Pattern, Sequence]:
    """if the application of the given pattern leads to perfect matchintg sequence,
    this method returns the sequence. otherwise, the pattern itself is returned
    """
    folded_dfg = dfg.copy()
    pattern.fold_dfg(folded_dfg)
    induced_sequence = find_isolated_sequence_from_candidate_node(
            folded_dfg, folded_dfg.nodes[pattern.get_activity_name()])
    if induced_sequence is not None:
        return induced_sequence
    else:
        return pattern

def _find_sequence_nodes_candidates(dfg: DirectlyFollowsGraph):
    start_candidates = set()
    part_candidates = set()
    for node in dfg.get_nodes():
        _add_node_to_start_or_part_candidates(
                dfg, node, start_candidates, part_candidates)

    return start_candidates, part_candidates

def _add_node_to_start_or_part_candidates(
        dfg: DirectlyFollowsGraph, node: Node, start_candidates: Set,
        part_candidates: Set):
    if dfg.compute_indegree(node.activity) <= 1:
        if len(node.edges) <= 1:
            part_candidates.add(node.activity)
    elif len(node.edges) == 1:
        start_candidates.add(node.activity)

def _construct_sequences(start_candidates: Set[str], part_candidates: Set[str],
                         dfg: DirectlyFollowsGraph):
    sequence_set = set()
    _construct_sequences_from_start_candidates(sequence_set, start_candidates,
                                               part_candidates, dfg)
    _construct_sequences_from_remaining_part_candidates(
            sequence_set, part_candidates, dfg)

    if isinstance(dfg, PatternDfg):
        for sequence in sequence_set:
            sequence.pattern_list = [dfg.nodes[p.activity].pattern
                                     for p in sequence.pattern_list]

    return sequence_set

def _construct_sequences_from_start_candidates(
        sequence_set, start_candidates: Set[str], part_candidates: Set[str],
        dfg: DirectlyFollowsGraph):
    for activity in start_candidates:
        _construct_sequences_from_start(activity, sequence_set,
                                        part_candidates, dfg)

def _construct_sequences_from_start(
        start_activity: str, sequence_set, part_candidates: Set[str],
        dfg: DirectlyFollowsGraph):
    sequence = [start_activity]
    start_node = dfg.nodes[start_activity]
    next_node = start_node.edges[0].end
    while dfg.compute_indegree(next_node.activity) == 1:
        sequence.append(next_node.activity)
        part_candidates.discard(next_node.activity)
        if not len(next_node.edges) == 1:
            break
        next_node = next_node.edges[0].end
        #cycle detection
        if len(sequence) > dfg.get_nr_of_nodes():
            return
    if len(sequence) > 1:
        #special case: sequence is part of a cycle and the last node has
        #an edge to the first one => remove last activity in sequence
        if start_activity in [e.end.activity for e in dfg.nodes[sequence[-1]].edges]:
            #removing the last element could lead to sequence of length 1,
            #however we are only interested in sequences of length >= 2
            if len(sequence) > 2:
                sequence_set.add(Sequence.from_activity_list(sequence[:-1]))
        else:
            sequence_set.add(Sequence.from_activity_list(sequence))

def _construct_sequences_from_remaining_part_candidates(
        sequence_set, part_candidates: Set[str], dfg: DirectlyFollowsGraph):
    added_activities = set()
    for activity in part_candidates:
        start_node = dfg.nodes[activity]
        if _is_valid_start_candidate(start_node, added_activities,
                                     part_candidates, dfg):
            sequence = [activity]
            next_node = start_node.edges[0].end
            while dfg.compute_indegree(next_node.activity) == 1:
                sequence.append(next_node.activity)
                if (not next_node.edges or len(next_node.edges) > 1):
                    break
                next_node = next_node.edges[0].end
                added_activities.add(next_node.activity)
                #cycle detection
                if len(sequence) > dfg.get_nr_of_nodes():
                    return
            if len(sequence) > 1:
                sequence_set.add(Sequence.from_activity_list(sequence))

def _is_valid_start_candidate(start_node, added_activities,
                              part_candidates, dfg) -> bool:
    """
    a start node must
      1. have an out-degree of 1
      2. not be part of an already constructed sequence
      3. not have an predecessor who is part of a sequence => maximal sequences
    """
    return (len(start_node.edges) == 1 and
            start_node.activity not in added_activities and
            not [activity for activity in dfg.get_preceeding_activities(
                    start_node.activity) if activity in part_candidates])