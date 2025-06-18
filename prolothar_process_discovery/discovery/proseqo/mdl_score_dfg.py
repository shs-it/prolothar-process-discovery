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
import prolothar_common.mdl_utils as mdl_utils

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import NR_OF_PATTERN_TYPES_WITH_SINGLETON
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence

from math import log2
from typing import Iterable

def compute_mdl_score_dfg(data: DirectlyFollowsGraph,
                          model: PatternDfg,
                          verbose=False) -> float:
    """computes the minimum description length of the given dfg and a model (dfg).
    this is MDL(model) + MDL(data|model)
    """
    expanded_model = model.expand()
    mdl_score = _compute_encoded_length_of_model(
            data, model, expanded_model, verbose)
    mdl_score += _compute_encoded_length_of_data_given_model(
            data, model, expanded_model, verbose)
    return mdl_score

def _compute_encoded_length_of_model(
        data: DirectlyFollowsGraph, model: PatternDfg,
        expanded_model: DirectlyFollowsGraph, verbose: bool) -> float:
    #nr of activities => |A|
    mdl_of_model = mdl_utils.L_N(data.get_nr_of_nodes())

    #nr of nodes, |A| is an upper bound
    mdl_of_model += log2(data.get_nr_of_nodes())

    #nr of edges or 0, |V|^2 is an upper bound for |E|
    max_nr_of_edges = model.get_nr_of_nodes() ** 2 - sum(
        node.pattern.get_nr_of_forbidden_edges_in_pattern_dfg(model)
        for node in model.get_nodes()
    )
    mdl_of_model += log2(max_nr_of_edges + 1)

    #which edges are present in the graph
    mdl_of_model += mdl_utils.log2binom(max_nr_of_edges, model.get_nr_of_edges())

    #sum of weights = nr of modeled moves, can be 0
    sum_of_weights = _compute_sum_of_weights(data, expanded_model)
    mdl_of_model += mdl_utils.L_N(sum_of_weights + 1)

    #which edge has which weight in the model?
    if expanded_model.get_nr_of_edges() > 0:
        if sum_of_weights < 1:
            model.plot()
            expanded_model.plot()
        mdl_of_model += mdl_utils.L_U(
                sum_of_weights, expanded_model.get_nr_of_edges())

    mdl_of_model += _encode_patterns_of_nodes(data, model.get_nodes())

    if verbose:
        print('L(M) = %.2f' % mdl_of_model)

    return mdl_of_model

def _encode_patterns_of_nodes(
        data: DirectlyFollowsGraph, nodes: Iterable[Node]) -> float:
    activity_set = frozenset(data.nodes.keys())
    mdl_of_patterns = 0
    for node in nodes:
        mdl_of_patterns += log2(NR_OF_PATTERN_TYPES_WITH_SINGLETON)
        #workaround for the fact that perfect matching but small sequences
        #are too expensive in comparison to single nodes => make nodes
        #more expensive by turning them into one element sequences
        if node.pattern.is_singleton():
            mdl_of_patterns += Sequence([node.pattern]).get_encoded_length_in_code_table(
                    activity_set)[0]
        else:
            mdl_of_patterns += node.pattern.get_encoded_length_in_code_table(
                    activity_set)[0]
    return mdl_of_patterns

def _compute_sum_of_weights(data: DirectlyFollowsGraph,
                            expanded_model: DirectlyFollowsGraph) -> int:
    sum_of_weights = 0
    for edge in expanded_model.get_edges():
        count_of_edge = max(1, data.get_count(edge.start.activity,
                                              edge.end.activity))
        sum_of_weights += count_of_edge
    return sum_of_weights

def _compute_encoded_length_of_data_given_model(
            data: DirectlyFollowsGraph, model: PatternDfg,
            expanded_model: DirectlyFollowsGraph, verbose: bool) -> float:

    mdl_of_data_given_model = _compute_mdl_of_e_minus(
            data, model, expanded_model, verbose)

    mdl_of_data_given_model += _compute_mdl_of_e_plus(
            data, model, expanded_model, verbose)

    mdl_of_data_given_model += _compute_mdl_of_v_plus(
            data, model, expanded_model, verbose)

    if verbose:
        print('L(D|M) = %.2f' % mdl_of_data_given_model)
    return mdl_of_data_given_model

def _compute_mdl_of_e_minus(
            data: DirectlyFollowsGraph, model: PatternDfg,
            expanded_model: DirectlyFollowsGraph, verbose: bool) -> float:
    #nr of edges that are only present in the model and must be removed
    #to restore the data. nr of edges in the model is an upper bound.
    #can be 0 (=> +1 )
    mdl_of_e_minus = log2(expanded_model.get_nr_of_edges() + 1)

    model_move_edges = set(expanded_model.edges.keys()).difference(
            set(data.edges.keys()))
    if model_move_edges:
        #which edges must be removed?
        mdl_of_e_minus += mdl_utils.log2binom(expanded_model.get_nr_of_edges(),
                                              len(model_move_edges))

    if verbose:
        print('L(E-) = %.2f' % mdl_of_e_minus)

    return mdl_of_e_minus

def _compute_mdl_of_e_plus(
            data: DirectlyFollowsGraph, model: PatternDfg,
            expanded_model: DirectlyFollowsGraph, verbose: bool) -> float:
    log_move_edges = set(data.edges.keys()).difference(
            set(expanded_model.edges.keys()))
    max_nr_of_edges_to_add = (
            data.get_nr_of_nodes()**2 - expanded_model.get_nr_of_edges())
    #nr of edges that are only present in the log and must be added
    #to restore the data. can be 0 (=> +1 )
    mdl_of_e_plus = log2(max_nr_of_edges_to_add + 1)

    #|A|^2 - |E+| gives the number of edges that can be added
    if log_move_edges:
        #which edges must be added?
        mdl_of_e_plus += mdl_utils.log2binom(max_nr_of_edges_to_add,
                                             len(log_move_edges))
        missing_edge_weight = sum(data.get_count(edge[0], edge[1])
                                  for edge in log_move_edges)
        mdl_of_e_plus += mdl_utils.L_N(missing_edge_weight)
        #which edge has which count?
        mdl_of_e_plus += mdl_utils.L_U(missing_edge_weight, len(log_move_edges))

    if verbose:
        print('L(E+) = %.2f' % mdl_of_e_plus)

    return mdl_of_e_plus

def _compute_mdl_of_v_plus(
            data: DirectlyFollowsGraph, model: PatternDfg,
            expanded_model: DirectlyFollowsGraph, verbose: bool) -> float:
    """encoding of nodes that are only present in the log and must be added
    to restore the data
    """
    missing_nodes = [node for node in data.get_nodes()
                     if node.activity not in expanded_model.nodes]
    mdl_of_v_plus = mdl_utils.L_N(len(missing_nodes) + 1)
    mdl_of_v_plus += _encode_patterns_of_nodes(data, missing_nodes)

    if verbose:
        print('L(V+) = %.2f' % mdl_of_v_plus)

    return mdl_of_v_plus
