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

from typing import List, Tuple, Set, Union

from prolothar_common.models.eventlog import EventLog
from prolothar_common.models.dfg.edge import Edge


from prolothar_process_discovery.discovery.proseqo.edge_removal.edge_removal_strategy import EdgeRemovalStrategy
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score

from prolothar_common.parallel.abstract.computation_engine import ComputationEngine
from prolothar_common.parallel.multiprocess.multiprocess import MultiprocessComputationEngine
from prolothar_common.parallel.single_thread.single_thread import SingleThreadComputationEngine

class RemoveEdgeWithHighestMdlGain(EdgeRemovalStrategy):
    """EdgeRemovalStrategy that for all edges individually computes the MDL of
    the PatternDFG given a log if one removes the edge. the one with the lowest
    increase of the MDL (or with the highest gain if applicable) is removed.
    Additionally, edges and nodes are removed if new sources or sinks are
    created by this single removed edge"""

    def __init__(self, allow_multiprocessing: bool = True,
                 evaluation_limit: Union[str,int] = None):
        """
        create and configures this PatternDfg EdgeRemovalStrategy

        Parameters
        ----------
        allow_multiprocessing : bool, optional
            If True, then multiple processors may be used for computations.
            The default is True.
        evaluation_limit : Union[str,int], optional
            Computing the gain of every edge in the graph can be very expensive.
            This parameter can control how many candidates are considered in
            one iteration. If the graph contains more than this edges, then
            the edges are sorted by their frequency and only the least frequent
            edges are considered. This parameter can either be a specific number
            such as 100 or it can be None (meaning no limit) or it can be the
            string "nodes", which means the current number of nodes is the
            limit for the number of edges that are examined.
        """
        self.__allow_multiprocessing = allow_multiprocessing
        self.__evaluation_limit = evaluation_limit

    def remove_edges(
            self, dfg: PatternDfg, log: EventLog,
            source_nodes: Set[str] = None, sink_nodes: Set[str] = None,
            verbose: bool = False) -> PatternDfg:

        if source_nodes is None:
            source_nodes = dfg.get_source_activities()
        if sink_nodes is None:
            sink_nodes = dfg.get_sink_activities()

        mdl_score, edge_key = self.__compute_edge_with_lowest_loss(
                dfg, log, source_nodes, sink_nodes)

        if verbose:
            print('remove %r, MDL: %r' % (edge_key, mdl_score))

        if edge_key:
            dfg.remove_edge(edge_key)

        return dfg

    def __create_computation_engine(self, dfg: PatternDfg,
                                    log: EventLog) -> ComputationEngine:
        if self.__allow_multiprocessing and dfg.get_nr_of_edges() > 200:
            return MultiprocessComputationEngine()
        else:
            return SingleThreadComputationEngine()

    def __repr__(self) -> str:
        return 'RemoveEdgeWithHighestMdlGain()'

    def __compute_edge_with_lowest_loss(
            self, dfg: PatternDfg, log: EventLog, source_nodes: Set[str],
            sink_nodes: Set[str]) -> List[Tuple[Edge,float]]:

        computation_engine = self.__create_computation_engine(dfg, log)

        candidate_edges = None
        if self.__evaluation_limit is None:
            candidate_edges = list(dfg.edges.values())
        elif isinstance(self.__evaluation_limit, int):
            candidate_edges = self.__get_n_least_frequent_non_cutting_edges(
                dfg, self.__evaluation_limit, source_nodes, sink_nodes)
        elif self.__evaluation_limit == 'nodes':
            candidate_edges = self.__get_n_least_frequent_non_cutting_edges(
                dfg, dfg.get_nr_of_nodes(), source_nodes, sink_nodes)

        if candidate_edges:
            return computation_engine\
                .create_partitionable_list(candidate_edges)\
                .map_reduce(
                    {'dfg': dfg, 'log': log,
                     'source_nodes': source_nodes,
                     'sink_nodes': sink_nodes},
                    _compute_score_for_edge, min)
        else:
            return None,None

    def __get_n_least_frequent_non_cutting_edges(
            self, dfg: PatternDfg, n: int, source_nodes: Set[str],
            sink_nodes: Set[str]) -> List[Edge]:
        edges = []
        for edge in sorted(dfg.get_edges(), key=lambda e: e.count):
            if len(edges) >= n:
                break
            if not _edge_is_cutting(edge, dfg, source_nodes, sink_nodes):
                edges.append(edge)
        return edges

def _edge_is_cutting(
        edge: Edge, dfg: PatternDfg, source_nodes: Set[str],
        sink_nodes: Set[str]) -> bool:
    """
    returns True if the removal of the edge would result in a loss of
    connectivity from source_nodes to sink_nodes. return False if not
    all nodes are reachable from at least one source or not all nodes
    can reach a sink.
    """
    activities_before_removal = set(dfg.nodes.keys())
    dfg.remove_edge((edge.start.activity, edge.end.activity))
    activities_after_removal = _get_connected_component(
        dfg, source_nodes, sink_nodes)
    dfg.add_count(edge.start.activity, edge.end.activity, edge.count)
    return activities_before_removal != activities_after_removal


def _compute_score_for_edge(parameters, edge):
    """computes the MDL of the pattern-dfg without the given edge"""
    dfg = parameters['dfg']
    if _edge_is_cutting(edge, dfg, parameters['source_nodes'],
                        parameters['sink_nodes']):
        mdl_score = float('inf')
    else:
        dfg.remove_edge((edge.start.activity, edge.end.activity))
        mdl_score = compute_mdl_score(parameters['log'], dfg, verbose=False)
        dfg.add_count(edge.start.activity, edge.end.activity, count=edge.count)
    return (mdl_score, (edge.start.activity, edge.end.activity))

def _get_connected_component(
        dfg: PatternDfg, source_nodes: Set[str], sink_nodes: Set[str]) -> Set[str]:
    reachable_activities_from_sources = set()
    for source in source_nodes:
        reachable_activities_from_sources.add(source)
        reachable_activities_from_sources.update(
            dfg.get_reachable_activities(source))

    activities_that_reach_a_sink = set()
    for sink in sink_nodes:
        activities_that_reach_a_sink.add(sink)
        activities_that_reach_a_sink.update(
            dfg.get_activities_that_reach(sink))

    return reachable_activities_from_sources.intersection(
        activities_that_reach_a_sink)
