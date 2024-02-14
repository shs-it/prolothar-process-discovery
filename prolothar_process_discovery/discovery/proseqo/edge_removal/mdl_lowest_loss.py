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

from prolothar_common.models.eventlog import EventLog

from prolothar_process_discovery.discovery.proseqo.edge_removal.edge_removal_strategy import EdgeRemovalStrategy
from prolothar_process_discovery.discovery.proseqo.edge_removal.remove_edge_with_highest_mdl_gain import RemoveEdgeWithHighestMdlGain
from prolothar_process_discovery.discovery.proseqo.edge_removal.termination_criterion import TerminationCriterion
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score

from prolothar_common.parallel.abstract.computation_engine import ComputationEngine
from prolothar_common.parallel.multiprocess.multiprocess import MultiprocessComputationEngine
from prolothar_common.parallel.single_thread.single_thread import SingleThreadComputationEngine


class MdlLowestLoss(EdgeRemovalStrategy):
    """EdgeRemovalStrategy that for all edges individually computes the MDL of
    the PatternDFG given a log if one removes the edge. the top N with the lowest
    increase of the MDL (or with the highest gain if applicable) are removed"""

    def __init__(self, termination_criterion: TerminationCriterion,
                 allow_multiprocessing: bool = True):
        self.__remove_single_edge_strategy = RemoveEdgeWithHighestMdlGain(
            allow_multiprocessing = allow_multiprocessing)
        self.__termination_criterion = termination_criterion

    def remove_edges(self, dfg: PatternDfg, log: EventLog, verbose=False):
        source_nodes = dfg.get_source_activities()
        sink_nodes = dfg.get_sink_activities()

        initial_dfg = dfg
        dfg = dfg.copy()
        if verbose:
            original_mdl_score = compute_mdl_score(log, dfg, verbose=False)
            print('MDL without any edges removed: %r' % original_mdl_score)
        while not self.__termination_criterion.should_terminate(
                initial_dfg, dfg, verbose=verbose):
            if dfg.get_nr_of_edges() == 0:
                break

            self.__remove_single_edge_strategy.remove_edges(
                dfg, log, source_nodes = source_nodes, sink_nodes = sink_nodes,
                verbose = verbose)

        return dfg.get_largest_weakly_connected_component()

    def __create_computation_engine(self, dfg: PatternDfg,
                                    log: EventLog) -> ComputationEngine:
        if self.__allow_multiprocessing and dfg.get_nr_of_edges() > 200:
            return MultiprocessComputationEngine()
        else:
            return SingleThreadComputationEngine()

    def __repr__(self) -> str:
        return 'MdlLowestLoss(%r)' % self.__termination_criterion