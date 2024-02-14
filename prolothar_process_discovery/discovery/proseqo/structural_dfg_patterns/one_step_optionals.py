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
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import return_induced_sequence_if_existing
from typing import Set

def find_one_step_optionals_in_dfg(
        dfg: DirectlyFollowsGraph,
        find_induced_sequences: bool = False,
        only_perfect_matches: bool = True) -> Set[Optional]:
    """returns optionals of one activity

    Args:
        dfg:
            The directly-follows-graph in which we want to find optional
            activities
        find_induced_sequences:
            default is False. If True, perfect matching sequences, which
            contain the found optionals are returned instead of the optionals
            themselves.
        only_perfect_matches:
            default is True. If True, only perfect matching optionals will be
            considered as candidates. Otherwise more nodes will be consideres
            as optionals

    Returns:
        a set of Optional patterns found in the dfg.
    """
    optionals = set()
    for node in dfg.get_nodes():
        if not only_perfect_matches or is_optional(node, dfg):
            optionals.add(Optional(Singleton(node.activity)))

    if isinstance(dfg, PatternDfg):
        for optional in optionals:
            optional.opt_pattern = dfg.nodes[optional.opt_pattern.activity].pattern

    if find_induced_sequences:
        induced_sequences = set()
        for optional in optionals:
            try:
                induced_sequences.add(
                        return_induced_sequence_if_existing(optional, dfg))
            except KeyError:
                #fix for rare, unreproducible error
                pass
        return induced_sequences
    else:
        return optionals

def is_optional(node, dfg):
    """returns True if the given node shows the pattern of an optional activity,
    i.e. for any predecessor there exists an edge to any ancestor of the given
    node
    """
    #self loops lead to wrong result in the following tests
    if node.is_followed_by(node.activity):
        return False

    #Optionals must have at least one predecessor and ancestor
    if not node.ingoing_edges or not node.edges:
        return False

    #All predecessor must be connected to all ancestors
    for ingoing_edge in node.ingoing_edges:
        for outgoing_edge in node.edges:
            if not ingoing_edge.start.is_followed_by(outgoing_edge.end.activity):
                return False

    return True
