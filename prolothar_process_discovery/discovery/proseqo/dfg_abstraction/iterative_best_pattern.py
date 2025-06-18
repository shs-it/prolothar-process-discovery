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

from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.dfg_abstraction_strategy import DfgAbstractionStrategy

from prolothar_common.models.eventlog import EventLog
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import find_isolated_sequences_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_loops import find_isolated_loops_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_choices import find_one_step_choices_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_optionals import find_one_step_optionals_in_dfg
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.cover import Cover
from prolothar_process_discovery.discovery.proseqo.greedy_cover import compute_cover
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score_given_cover
from prolothar_process_discovery.discovery.proseqo.mdl_score import estimate_lower_bound_mdl_score

from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidate_evaluation_worker import CandidateEvaluationWorker
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidate_evaluation_worker import SingleThreadCandidateEvaluationWorker
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import Candidate
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.pattern import CandidatePattern
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import apply_candidate
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import infer_candidates
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import merge_candidates
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.candidate_generator import CandidateGenerator

from prolothar_common.collections import list_utils

import psutil
from multiprocessing import Queue
from queue import Queue as QQueue

from typing import Set, Tuple, List, Union, Dict
from collections import Counter

import heapq

from datetime import timedelta, datetime

class SearchState():
    """
    describes the state of the current search. this is used internally in
    IterativeBestPattern
    """

    def __init__(self, initial_mdl: float, intitial_cover: Cover,
                 initial_model: PatternDfg, selected_candidates: List[Candidate]):
        self.remaining_candidates: List[Tuple[float, Candidate]] = []
        #candidates, that should not be added to the candidate set again
        self.locked_candidates: Set[Candidate] = set()
        self.nr_of_remaining_candidates_per_type: Counter = Counter()
        self.current_mdl = initial_mdl
        self.current_cover: Cover = intitial_cover
        self.current_model: PatternDfg = initial_model
        self.selected_candidates: List[Candidate] = selected_candidates

class IterativeBestPattern(DfgAbstractionStrategy):
    """implementation of DfgAbstractionStrategy that greedily applies patterns
    in order of their MDL gain
    """

    def __init__(self,
                 candidate_generator: CandidateGenerator,
                 timebudget: timedelta = None,
                 max_nr_of_workers: int = psutil.cpu_count(),
                 multiple_iterations: bool = False,
                 use_estimated_mdl_for_candidate_generation: bool = False,
                 candidate_pruning: bool = False,
                 evaluation_limit: Union[None, str] = None,
                 apply_trivial_patterns: bool = True,
                 prune_with_lower_bound_estimates: bool = False):
        """creates a new instance of this dfg abstraction strategy

        Args:
            candidate_generator:
                used to generate new candidates during search. new candidates
                are added when
                - at beginning of the search
                - a analyzed candidate is added to the set of selected candidates
                - a anlyzed candidate is not added to the set of selected
                  candidates, but "add_new_candidates_if_candidate_fails = True"
            add_new_candidates_if_candidate_fails:
                default is False. If True, then new candidates are generated
                if the application of a candidate itself does lead to a lower
                MDL.
            timebudget:
                if a timedelta is given, candidate analysis terminates after
                this amount of time. if None, there is no time limit.
            multiple_iterations:
                starts a new search with empty locked candidate set while
                the pattern graph changes
            max_nr_of_workers:
                default is nr of available CPU cores.
            use_estimated_mdl_for_candidate_generation:
                default is False. If True, an estimated MDL is used to insert
                a candidate into the priority list (or to determine not in
                insert it at all). This speeds up computation.
            candidate_pruning:
                default is False. If True, when a candidate is successfully
                applied, other candidates still waiting in the priortity queue
                are pruned, i.e. contradicting candidates are removed
            evaluation_limit:
                default is None, i.e. no limit. If equal to "nodes" then the
                number of nodes will limit the number of new candidates that
                are evaluated in one iteration
        """
        self.__candidate_generator = candidate_generator
        self.__timebudget = timebudget
        self.__candidate_evaluation_workers = []
        self.__max_nr_of_workers = min(max_nr_of_workers, psutil.cpu_count())
        if self.__max_nr_of_workers > 1:
            self.__candidate_evaluation_result_queue = Queue()
        else:
            self.__candidate_evaluation_result_queue = QQueue()
        self.__multiple_iterations = multiple_iterations
        self.__use_estimated_mdl_for_candidate_generation = \
            use_estimated_mdl_for_candidate_generation
        self.__candidate_pruning = candidate_pruning
        self.__evaluation_limit = evaluation_limit
        self.__apply_trivial_patterns = apply_trivial_patterns
        self.__prune_with_lower_bound_estimates = prune_with_lower_bound_estimates

    def mine_dfg(self, log: EventLog, dfg: DirectlyFollowsGraph,
                 selected_candidates: List[Candidate] = None,
                 verbose: bool = False, start_time = None):
        if start_time is None:
            start_time = datetime.now()
        if verbose:
            print('pattern search started at %r' % start_time)
            print('log has %d traces' % log.get_nr_of_traces())
        original_dfg = PatternDfg.create_from_event_log(log)
        folded_dfg = PatternDfg.create_from_dfg(dfg)
        activity_supports = log.compute_activity_supports()
        activity_set = set(activity_supports.keys())

        self.__init_and_start_candidate_evaluation_workers(original_dfg, log)

        if selected_candidates is None:
            selected_candidates = infer_candidates(original_dfg, folded_dfg)

        for candidate in selected_candidates:
            candidate.apply_on_dfg(folded_dfg)
        nr_of_nodes_at_start = folded_dfg.get_nr_of_nodes()
        nr_of_edges_at_start = folded_dfg.get_nr_of_edges()
        candidate_cover = compute_cover(log.traces, dfg, activity_set=activity_set)
        candidate_mdl = compute_mdl_score_given_cover(candidate_cover, log,
                                                      folded_dfg)
        search_state = SearchState(
            candidate_mdl, candidate_cover, folded_dfg, selected_candidates)

        if verbose:
            print('start with MDL %.2f' % search_state.current_mdl)
            print('Nr of nodes: %d' % nr_of_nodes_at_start)
            print('Nr of edges: %d' % nr_of_edges_at_start)
        if self.__apply_trivial_patterns:
            folded_dfg, selected_candidates = self.__fold_with_perfect_sequences(
                    folded_dfg, original_dfg, selected_candidates)
        while not search_state.remaining_candidates:
            if not self.__add_new_candidates(
                    original_dfg, log,
                    self.__candidate_generator,
                    activity_supports, search_state, verbose):
                if verbose:
                    print('no new candidates found')
                break

        while search_state.remaining_candidates \
        and not self.__is_timebudget_exceeded(start_time):
            if verbose:
                print('remaining candidates: %d' % len(
                    search_state.remaining_candidates))
            estimated_gain, current_candidate = heapq.heappop(
                search_state.remaining_candidates)
            self.__examine_current_candidate(
                current_candidate, estimated_gain, original_dfg, log,
                activity_supports, activity_set, search_state, verbose)
            while not search_state.remaining_candidates:
                if not self.__add_new_candidates(
                        original_dfg, log, self.__candidate_generator,
                        activity_supports, search_state, verbose):
                    if verbose:
                        print('no new candidates found')
                    break

        if verbose and self.__timebudget and (
                datetime.now() - start_time) > self.__timebudget:
            print('aborted pattern search due to timebudget')

        if verbose:
            print('terminate worker processes')

        self.__terminate_workers()

        if verbose:
            print('pattern search completed at %r' % datetime.now())

        if not self.__multiple_iterations or (
                search_state.current_model.get_nr_of_nodes() == nr_of_nodes_at_start and
                search_state.current_model.get_nr_of_edges() == nr_of_edges_at_start):
            if verbose:
                print('stop search. parameter multiple_iterations is %r' %
                      self.__multiple_iterations)
            if self.__apply_trivial_patterns:
                self.__fold_with_perfect_patterns(search_state.current_model)
            search_state.current_model.remove_degenerated_patterns()
            return search_state.current_model
        else:
            if verbose:
                print('start a new iteration')
            return self.mine_dfg(
                    log, dfg,
                    selected_candidates=search_state.selected_candidates,
                    verbose=verbose, start_time=start_time)

    def __prune_start_end_nodes(
            self, folded_dfg: PatternDfg, original_dfg: DirectlyFollowsGraph):
        allowed_start_activities = set()
        for original_start_activity in original_dfg.get_source_activities():
            allowed_start_activities.update(
                pattern.get_activity_name() for pattern in
                folded_dfg.get_patterns_with_activity(original_start_activity))
        folded_dfg.remove_not_allowed_start_activities(allowed_start_activities)

        allowed_end_activities = set()
        for original_end_activity in original_dfg.get_sink_activities():
            allowed_end_activities.update(
                pattern.get_activity_name() for pattern in
                folded_dfg.get_patterns_with_activity(original_end_activity))
        folded_dfg.remove_not_allowed_end_activities(allowed_end_activities)


    def __init_and_start_candidate_evaluation_workers(
            self, original_dfg: DirectlyFollowsGraph, log: EventLog):
        if self.__max_nr_of_workers > 1:
            self.__candidate_evaluation_workers = []
            for _ in range(self.__max_nr_of_workers):
                worker = CandidateEvaluationWorker(
                        original_dfg, log,
                        self.__candidate_evaluation_result_queue,
                        self.__use_estimated_mdl_for_candidate_generation)
                worker.start()
                self.__candidate_evaluation_workers.append(worker)
        else:
            self.__candidate_evaluation_workers = [
                SingleThreadCandidateEvaluationWorker(
                    original_dfg, log,
                    self.__candidate_evaluation_result_queue,
                    self.__use_estimated_mdl_for_candidate_generation)
            ]

    def __terminate_workers(self):
        for worker in self.__candidate_evaluation_workers:
            worker.terminate()
            worker.join()
        self.__candidate_evaluation_workers.clear()

    def __is_timebudget_exceeded(self, start_time) -> bool:
        return self.__timebudget is not None and (
                datetime.now() - start_time) > self.__timebudget

    def __examine_current_candidate(
            self, current_candidate: Candidate, estimated_gain: float,
            original_dfg: PatternDfg, log: EventLog,
            activity_supports: Dict[str, int],
            activity_set: Set[str],
            search_state: SearchState, verbose: bool) -> Tuple[PatternDfg, float]:
        search_state.nr_of_remaining_candidates_per_type[
                type(current_candidate).__name__] -= 1

        candidate_dfg, candidate_set = apply_candidate(
                original_dfg, search_state.selected_candidates, current_candidate)
        self.__prune_start_end_nodes(candidate_dfg, original_dfg)
        candidate_cover = compute_cover(log.traces, candidate_dfg, activity_set=activity_set)
        candidate_mdl = compute_mdl_score_given_cover(candidate_cover, log,
                                                      candidate_dfg)
        if candidate_mdl < search_state.current_mdl:
            if verbose:
                print('apply (%r, %.2f) => decreases mdl from %.2f to %.2f' % (
                        current_candidate, estimated_gain, search_state.current_mdl,
                        candidate_mdl))
                search_state.current_model = candidate_dfg
                search_state.current_mdl = candidate_mdl
                search_state.selected_candidates = candidate_set
                search_state.current_cover = candidate_cover
                if self.__candidate_pruning:
                    self.__prune_candidates(log, original_dfg, search_state)
                self.__add_new_candidates(
                        original_dfg,
                        log, self.__candidate_generator,
                        activity_supports, search_state,
                        verbose)
        else:
            if verbose:
                print('apply (%r, %.2f) => could not decrease mdl %.2f >= %.2f' % (
                      current_candidate, estimated_gain, candidate_mdl,
                      search_state.current_mdl))

    def __prune_candidates(
            self, log: EventLog, original_dfg: DirectlyFollowsGraph,
            search_state: SearchState) -> List[Tuple[float, Candidate]]:
        search_state.nr_of_remaining_candidates_per_type.clear()
        still_generated_candidates = self.__candidate_generator.generate_candidates(
                log, original_dfg, search_state.current_model)
        remaining_candidates = []
        for gain,candidate in remaining_candidates:
            if candidate in still_generated_candidates:
                remaining_candidates.append((gain,candidate))
                search_state.nr_of_remaining_candidates_per_type[
                        type(candidate).__name__] += 1
        heapq.heapify(remaining_candidates)
        return remaining_candidates

    def __add_new_candidates(
            self, original_dfg: PatternDfg, log: EventLog,
            candidate_generator: CandidateGenerator,
            activity_supports: Dict[str, int], search_state: SearchState,
            verbose: bool) -> bool:

        if verbose:
            print('search for new candidates started. current MDL: %.2f' %
                  search_state.current_mdl)

        new_candidates = candidate_generator.generate_candidates(
                log, original_dfg, search_state.current_model)
        new_candidates.difference_update(search_state.locked_candidates)
        new_candidates = self.__limit_new_candidates(
            new_candidates, original_dfg,
            search_state.nr_of_remaining_candidates_per_type, activity_supports,
            verbose)
        if self.__prune_with_lower_bound_estimates:
            new_candidates = self.__prune_new_candidates_using_lower_bound_estimate(
                new_candidates, search_state, log, original_dfg, verbose
            )

        if not new_candidates:
            return False

        if verbose:
            print('evaluate gain of %d new candidates' % len(new_candidates))

        nr_of_processing_workers = 0
        for i,new_candidates_partition in enumerate(list_utils.view_of_n_partitions(
                new_candidates, len(self.__candidate_evaluation_workers))):
            worker = self.__candidate_evaluation_workers[i]
            worker.evaluate_candidates(new_candidates_partition,
                                       search_state.current_mdl,
                                       search_state.selected_candidates)
            nr_of_processing_workers += 1

        while nr_of_processing_workers > 0:
            result = self.__candidate_evaluation_result_queue.get()
            if result is None:
                nr_of_processing_workers -= 1
            elif isinstance(result[0], Exception):
                self.__terminate_workers()
                print(result[1])
                print(search_state.selected_candidates)
                print(original_dfg.nodes.keys())
                raise result[0]
            else:
                #lowest priority is popped first
                #largest mdl_gain should be popped first
                #=> -mdl_gain is the priority
                search_state.nr_of_remaining_candidates_per_type[
                    type(result[1]).__name__] += 1
                heapq.heappush(
                    search_state.remaining_candidates, (-result[0], result[1]))
        search_state.locked_candidates.update(new_candidates)

        if verbose:
            print('search for new candidates completed')

        return True

    def __prune_new_candidates_using_lower_bound_estimate(
            self, new_candidates: List[Candidate], search_state: SearchState,
            log: EventLog, dfg: DirectlyFollowsGraph, verbose: bool):
        if verbose:
            print('candidates before pruning by mdl estimate: %d' % len(new_candidates))
        pruned_candidates = []
        for candidate in new_candidates:
            if estimate_lower_bound_mdl_score(
                    search_state.current_model, search_state.current_cover,
                    candidate, log, dfg) < search_state.current_mdl:
                pruned_candidates.append(candidate)
                search_state.locked_candidates.add(candidate)
        if verbose:
            print('candidates after pruning by mdl estimate: %d' % len(pruned_candidates))
        return pruned_candidates

    def __limit_new_candidates(
            self, new_candidates: Set[Candidate],
            dfg: PatternDfg,
            nr_of_remaining_candidates_per_type: Counter,
            activity_supports: Dict[str, int],
            verbose: bool) -> List[Candidate]:
        if self.__evaluation_limit == 'nodes':
            nr_of_remaining_candidates_per_type = Counter(nr_of_remaining_candidates_per_type)
            limited_candidates = []
            for _,candidate in sorted(
                    (c.get_frequency_priority(activity_supports), c)
                    for c in new_candidates):
                candidate_type = type(candidate).__name__
                if nr_of_remaining_candidates_per_type[
                        candidate_type] < dfg.get_nr_of_nodes():
                    limited_candidates.append(candidate)
                    nr_of_remaining_candidates_per_type[candidate_type] += 1
            if verbose and len(new_candidates) > len(limited_candidates):
                print('limited candidates from %d to %d' % (
                    len(new_candidates), len(limited_candidates)))
            return limited_candidates
        else:
            return list(new_candidates)

    def __fold_with_perfect_sequences(
            self, folded_dfg: PatternDfg, dfg: PatternDfg,
            selected_candidates: List[Candidate]) -> Tuple[PatternDfg, List[Candidate]]:
        sequences = find_isolated_sequences_in_dfg(folded_dfg)
        if sequences:
            selected_candidates = merge_candidates(
                    selected_candidates,
                    [CandidatePattern(s) for s in sequences])
            folded_dfg = dfg.copy()
            for candidate in selected_candidates:
                candidate.apply_on_dfg(folded_dfg)
        return folded_dfg, selected_candidates

    def __fold_with_perfect_patterns(
            self, folded_dfg: PatternDfg) -> Tuple[PatternDfg, List[Candidate]]:
        change_in_iteration = True
        #I do not know why but in a rare cases after hours of experiments,
        #some patterns lead to a error
        locked_patterns = set()
        while change_in_iteration:
            change_in_iteration = False
            for pattern_finder in [
                    find_isolated_sequences_in_dfg,
                    find_one_step_choices_in_dfg,
                    find_one_step_optionals_in_dfg,
                    find_isolated_loops_in_dfg]:
                patterns = set(pattern_finder(folded_dfg))
                patterns.difference_update(locked_patterns)
                if patterns:
                    change_in_iteration = True
                for pattern in patterns:
                    try:
                        pattern.fold_dfg(folded_dfg)
                    except KeyError:
                        locked_patterns.add(pattern)

    def __repr__(self) -> str:
        return ('IterativeBestPattern(\n'
                      'candidate_generator=%r,\n  '
                      'multiple_iterations=%r,\n  '
                      'timebudget=%r\n  '
                      'mdl_estimations=%r'
                      ')') % (
                self.__candidate_generator,
                self.__multiple_iterations,
                self.__timebudget,
                self.__use_estimated_mdl_for_candidate_generation)








