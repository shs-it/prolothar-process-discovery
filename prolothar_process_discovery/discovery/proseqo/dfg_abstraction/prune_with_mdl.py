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

from typing import Union, Set, Tuple

from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.dfg_abstraction_strategy import DfgAbstractionStrategy

from prolothar_common.models.eventlog import EventLog
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.dfg.edge import Edge
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import find_isolated_sequences_in_dfg
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.edge_removal import CandidateEdgeRemoval
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score
from prolothar_process_discovery.discovery.proseqo.mdl_score import estimate_mdl_score
from prolothar_process_discovery.discovery.proseqo.greedy_cover import compute_cover
from prolothar_process_discovery.discovery.proseqo.edge_removal.termination_criterion import TerminationCriterion

from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_loops import find_isolated_loops_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_choices import find_one_step_choices_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_optionals import find_one_step_optionals_in_dfg

from prolothar_process_discovery.discovery.proseqo.edge_removal.remove_edge_with_highest_mdl_gain import _compute_score_for_edge
from prolothar_process_discovery.discovery.proseqo.edge_removal.remove_edge_with_highest_mdl_gain import RemoveEdgeWithHighestMdlGain
from prolothar_process_discovery.discovery.proseqo.edge_removal.remove_edge_with_highest_mdl_gain import _edge_is_cutting

import heapq

from dataclasses import dataclass

class PruneWithMdl(DfgAbstractionStrategy):
    """implementation of DfgAbstractionStrategy that removes edges and folds
    the graph using perfectly matching patterns until some condition
    (e.g. a graph densitiy threshold) holds
    """

    def __init__(self, termination_criterion: TerminationCriterion,
                 allow_multiprocessing: bool = True,
                 evaluation_limit: Union[str,int] = None,
                 recompute_gain_in_every_iteration: bool = True,
                 use_mdl_estimations: bool = False,
                 reweight_edges: bool = False):
        """
        create and configures this PatternDfg pruning strategy

        Parameters
        ----------
        termination_criterion : TerminationCriterion
            determines when to stop the pruning.
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
        recompute_gain_in_every_iteration : bool, optional
            if True, then the MDL gain is recomputed for all canidates in every
            iteration. Otherwise, the gain of the last iteration is seen as a
            upperbound for the gain in the current iteration. the gain is only
            recomputed for the head of the priority queue to determine the next
            candidate. Default is True.
        use_mdl_estimations : bool, optional
            if True, then the MDL gain is computed by using a estimated MDL
            score which is supposed to be less precise but much faster.
            Default is False.
        reweight_edges : bool, optional
            if True, then the count-values of the edges are reweighted after
            pruning using a cover computation.
            Default is False.
        """
        self.__termination_criterion = termination_criterion
        self.__recompute_gain_in_every_iteration = recompute_gain_in_every_iteration
        self.__evaluation_limit = evaluation_limit
        self.__allow_multiprocessing = allow_multiprocessing
        self.__use_mdl_estimations = use_mdl_estimations
        if self.__recompute_gain_in_every_iteration and self.__use_mdl_estimations:
            raise NotImplementedError(
                'mdl estimations not allowed if gain is recomputed')
        self.__reweight_edges = reweight_edges

    def mine_dfg(self, log: EventLog, dfg: DirectlyFollowsGraph,
                 verbose: bool = False):
        pattern_dfg = PatternDfg.create_from_dfg(dfg)
        nr_of_sources = len(pattern_dfg.get_source_activities())
        nr_of_sinks = len(pattern_dfg.get_sink_activities())

        if self.__recompute_gain_in_every_iteration:
            remove_single_edge_strategy = RemoveEdgeWithHighestMdlGain(
                allow_multiprocessing = self.__allow_multiprocessing,
                evaluation_limit = self.__evaluation_limit)
        else:
            remove_single_edge_strategy = _FastRemoveEdgeWithHighestMdlGain(
                evaluation_limit = self.__evaluation_limit,
                use_mdl_estimations = self.__use_mdl_estimations)

        while not self.__termination_criterion.should_terminate(
                dfg, pattern_dfg, verbose=verbose) \
        and dfg.get_nr_of_edges() > 0:
            try:
                pattern_dfg = remove_single_edge_strategy.remove_edges(
                    pattern_dfg, log, verbose = verbose)
                pattern_dfg = self.__apply_patterns(pattern_dfg, nr_of_sources, nr_of_sinks)
            except StopIteration as e:
                if verbose:
                    print(e)
                break

        pattern_dfg = self.__apply_patterns(pattern_dfg, nr_of_sources, nr_of_sinks)

        if self.__reweight_edges:
            cover = compute_cover(log.traces, pattern_dfg,
                                  store_patterns_in_pattern_stream=True)
            pattern_dfg = cover.get_pattern_dfg_with_restored_counts()

        return pattern_dfg

    def __apply_patterns(
            self, pattern_dfg: PatternDfg, nr_of_sources: int,
            nr_of_sinks: int) -> PatternDfg:
        change = False
        change_in_iteration = True
        while change_in_iteration:
            change_in_iteration = False
            for pattern_finder in [
                    find_isolated_sequences_in_dfg,
                    find_isolated_loops_in_dfg,
                    find_one_step_choices_in_dfg,
                    find_one_step_optionals_in_dfg]:
                patterns = pattern_finder(pattern_dfg)
                if patterns:
                    for pattern in patterns:
                        last_pattern_dfg = pattern_dfg
                        pattern_dfg = pattern_dfg.copy()
                        try:
                            pattern.fold_dfg(pattern_dfg)
                            if len(pattern_dfg.get_sink_activities()) != nr_of_sinks:
                                pattern_dfg.remove_node(pattern.get_activity_name())
                                old_source_nodes = last_pattern_dfg.get_source_nodes()
                                pattern_dfg.remove_not_allowed_end_activities(
                                    new_node.activity
                                    for new_node in pattern_dfg.get_source_nodes()
                                    if [old_node for old_node in old_source_nodes
                                        if new_node.pattern.get_activity_set(
                                                ).intersection(
                                                    old_node.pattern.get_activity_set())]
                                    )
                        except Exception:
                            pattern_dfg = last_pattern_dfg
                        change_in_iteration = True
                        change = True
        if change:
            pattern_dfg.remove_degenerated_patterns()

        if len(pattern_dfg.get_source_activities()) != nr_of_sources \
        or len(pattern_dfg.get_sink_activities()) != nr_of_sinks:
            return last_pattern_dfg

        return pattern_dfg

    def __repr__(self) -> str:
        return 'PruneWithMdl(%r)' % self.__termination_criterion

class _FastRemoveEdgeWithHighestMdlGain():

    def __init__(self, evaluation_limit: Union[str,int] = None,
                 use_mdl_estimations: bool = False):
        self.__evaluation_limit = evaluation_limit
        self.__candidate_queue = []
        self.__waiting_queue = []
        self.__current_mdl = None
        self.__use_mdl_estimations = use_mdl_estimations
        self.__dfg = None
        self.__created_edges = set()

    def remove_edges(self, pattern_dfg: PatternDfg, log: EventLog,
                     verbose: bool = False) -> PatternDfg:
        if verbose:
            print('%d candidates in queue, %d additional are waiting' % (
                len(self.__candidate_queue), len(self.__waiting_queue)))
        if self.__dfg is None:
            self.__dfg = PatternDfg.create_from_event_log(log)
        if self.__use_mdl_estimations:
            self.__current_cover = compute_cover(log.traces, pattern_dfg)
        source_nodes = pattern_dfg.get_source_activities()
        sink_nodes = pattern_dfg.get_sink_activities()
        if not self.__candidate_queue and not self.__waiting_queue:
            self.__current_mdl = compute_mdl_score(log, pattern_dfg)
            self.__initialize_queues(pattern_dfg, source_nodes, sink_nodes, log)
            if not self.__candidate_queue:
                raise StopIteration('no more candidates')
            candidate_queue_length = len(self.__candidate_queue)
        else:
            candidate_queue_length = len(self.__candidate_queue)
            self.__prune_non_applicable_edges(pattern_dfg)
            self.__add_new_applicable_edges_to_waiting_queue(pattern_dfg)
        self.__remove_next_edge(pattern_dfg, source_nodes, sink_nodes, log,
                                verbose)
        self.__prune_non_applicable_edges(pattern_dfg)
        self.__add_new_applicable_edges_to_waiting_queue(pattern_dfg)

        while self.__waiting_queue \
        and len(self.__candidate_queue) < candidate_queue_length:
            self.__insert_edge_into_candidate_queue(
                self.__waiting_queue.pop(), pattern_dfg,
                source_nodes, sink_nodes, log)

        return pattern_dfg

    def __prune_non_applicable_edges(self, pattern_dfg: PatternDfg):
        """through pattern folding, the edge set of graph can have changed"""
        new_candidate_queue = []
        for candidate in self.__candidate_queue:
            if candidate.gain != float('inf') \
            and candidate.get_edge_key() in pattern_dfg.edges:
                heapq.heappush(new_candidate_queue, candidate)
        self.__candidate_queue = new_candidate_queue

        self.__waiting_queue = [edge for edge in self.__waiting_queue
                                if (edge.start.activity, edge.end.activity) in
                                pattern_dfg.edges]

    def __add_new_applicable_edges_to_waiting_queue(self, pattern_dfg: PatternDfg):
        """through pattern folding, the edge set of graph can have changed"""
        new_edges = set(pattern_dfg.get_edges()).difference(self.__created_edges)
        if new_edges:
            for edge in new_edges:
                self.__created_edges.add(edge)
                self.__waiting_queue.append(edge)
            self.__waiting_queue.sort(
                key=lambda edge: (-edge.count, edge.start.activity,
                                  edge.end.activity))

    def __initialize_queues(
            self, pattern_dfg: PatternDfg, source_nodes: Set[str],
            sink_nodes: Set[str], log: EventLog):
        evaluation_limit = self.__evaluation_limit
        if evaluation_limit is None:
            evaluation_limit = pattern_dfg.get_nr_of_edges()
        elif evaluation_limit == 'nodes':
            evaluation_limit = pattern_dfg.get_nr_of_nodes()
        edges = set(pattern_dfg.get_edges()).difference(self.__created_edges)
        edges = list(sorted(edges, key = lambda edge: (
            edge.count, edge.start.activity, edge.end.activity)))
        for edge in edges[:evaluation_limit]:
            self.__insert_edge_into_candidate_queue(
                edge, pattern_dfg, source_nodes, sink_nodes, log)
        self.__waiting_queue = edges[evaluation_limit:][::-1]
        self.__created_edges.update(edges)

    def __insert_edge_into_candidate_queue(
            self, edge: Edge, pattern_dfg: PatternDfg, source_nodes: Set[str],
            sink_nodes: Set[str], log: EventLog):
        try:
            mdl_without_edge = self.__compute_mdl_for_edge_removal(
                edge, pattern_dfg, source_nodes, sink_nodes, log)
            heapq.heappush(self.__candidate_queue, _Candidate(
                edge, mdl_without_edge - self.__current_mdl, True))
        except NotImplementedError as e:
            #a rare error that happens after hours of computation and thus
            #hard to reproduce
            if not 'more than one matching pattern' in str(e):
                raise e
            #message looks like this:
            #more than one matching pattern for "activity"
            duplicated_activity = str(e).replace(
                'more than one matching pattern for ', '')[1:-1]
            matching_nodes = [node for node in pattern_dfg.get_nodes()
                              if node.pattern.contains_activity(
                                      duplicated_activity)]
            if not matching_nodes:
                raise ValueError((str(e), duplicated_activity))
            for node in matching_nodes:
                if node.pattern.is_singleton() or \
                (len(node.edges) == 0 and len(node.ingoing_edges) == 0):
                    pattern_dfg.remove_node(node.activity)
            matching_nodes = [node for node in pattern_dfg.get_nodes()
                              if node.pattern.contains_activity(
                                      duplicated_activity)]
            if len(matching_nodes) > 1:
                print([node.activity for node in matching_nodes])
                raise NotImplementedError()

    def __compute_mdl_for_edge_removal(
                self, edge: Edge, pattern_dfg: PatternDfg, source_nodes: Set[str],
                sink_nodes: Set[str], log: EventLog) -> float:
        if self.__use_mdl_estimations:
            if _edge_is_cutting(edge, pattern_dfg, source_nodes, sink_nodes):
                return float('inf')
            return estimate_mdl_score(
                pattern_dfg, self.__current_cover, CandidateEdgeRemoval([edge]),
                log, self.__dfg)
        else:
            return _compute_score_for_edge(
                {'dfg': pattern_dfg, 'log': log,
                 'sink_nodes': sink_nodes,
                 'source_nodes': source_nodes}, edge)[0]

    def __remove_next_edge(
            self, pattern_dfg: PatternDfg, source_nodes: Set[str],
            sink_nodes: Set[str], log: EventLog, verbose: bool):
        while self.__candidate_queue:
            candidate = heapq.heappop(self.__candidate_queue)
            if candidate.gain != float('inf'):
                if candidate.gain_valid:
                    if verbose:
                        print('remove %r with count %d and gain %r' % (
                            candidate.get_edge_key(), candidate.edge.count,
                            candidate.gain))
                    pattern_dfg.remove_edge(candidate.get_edge_key())
                    for candidate in self.__candidate_queue:
                        if candidate.gain != float('inf'):
                            candidate.gain_valid = False
                    break
                else:
                    self.__insert_edge_into_candidate_queue(
                        candidate.edge, pattern_dfg, source_nodes, sink_nodes, log)

@dataclass
class _Candidate():
    edge: Edge
    gain: float
    gain_valid: bool

    def __lt__(self, other) -> bool:
        if self.gain == other.gain:
            return self.get_edge_key() < other.get_edge_key()
        return self.gain < other.gain

    def get_edge_key(self) -> Tuple[str,str]:
        return (self.edge.start.activity, self.edge.end.activity)

