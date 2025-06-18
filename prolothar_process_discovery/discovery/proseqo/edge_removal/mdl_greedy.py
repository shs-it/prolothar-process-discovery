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

from typing import List, Tuple

from prolothar_common.models.eventlog import EventLog
from prolothar_common.models.dfg.edge import Edge


from prolothar_process_discovery.discovery.proseqo.edge_removal.edge_removal_strategy import EdgeRemovalStrategy
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score

from prolothar_common.parallel.abstract.computation_engine import ComputationEngine
from prolothar_common.parallel.multiprocess.multiprocess import MultiprocessComputationEngine
from prolothar_common.parallel.single_thread.single_thread import SingleThreadComputationEngine

class MdlGreedy(EdgeRemovalStrategy):
    """EdgeRemovalStrategy that for all edges individually computes the MDL of
    the PatternDFG given a log if one removes the edge. all edges that decrease
    the length after removal will be removed"""

    def __init__(self, allow_multiprocessing=True):
        self.__allow_multiprocessing = allow_multiprocessing

    def remove_edges(self, dfg: PatternDfg, log: EventLog,
        verbose=False):

        dfg = dfg.copy()
        if dfg.get_nr_of_edges() > 0:
            original_mdl_score = compute_mdl_score(log, dfg, verbose=False)
            if verbose:
                print('MDL without any edges removed: %r' % original_mdl_score)

            for edge_key, mdl_score in self.__compute_greedy_redundant_edges(
                    dfg, log, original_mdl_score, verbose=verbose):
                if verbose:
                    print('remove %r, isolated MDL: %r' % (edge_key, mdl_score))
                dfg.remove_edge(edge_key)

        return dfg.get_largest_weakly_connected_component()

    def __create_computation_engine(self, dfg: PatternDfg,
                                    log: EventLog) -> ComputationEngine:
        if self.__allow_multiprocessing and dfg.get_nr_of_edges() > 200:
            return MultiprocessComputationEngine()
        else:
            return SingleThreadComputationEngine()

    def __repr__(self) -> str:
        return 'MdlGreedy'

    def __compute_greedy_redundant_edges(
            self, dfg: PatternDfg, log: EventLog, original_mdl_score: float,
            verbose=False) -> List[Tuple[Edge,float]]:

        computation_engine = self.__create_computation_engine(dfg, log)

        return computation_engine\
            .create_partitionable_list(list(dfg.edges.values()))\
            .map_filter(
                {'dfg': dfg, 'log': log, 'original_mdl': original_mdl_score},
                _compute_score_for_edge, _mdl_decreased)

def _compute_score_for_edge(parameters, edge):
    """computes the MDL of the pattern-dfg without the given edge"""
    copy_of_dfg = parameters['dfg'].copy()
    copy_of_dfg.remove_edge((edge.start.activity, edge.end.activity))
    mdl_score = compute_mdl_score(parameters['log'], copy_of_dfg, verbose=False)
    return ((edge.start.activity, edge.end.activity), mdl_score)

def _mdl_decreased(parameters, edge_and_score) -> bool:
    return edge_and_score[1] < parameters['original_mdl']