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

from multiprocessing import Process, Queue
from typing import List

from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import Candidate
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import apply_candidate
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import merge_candidates

from prolothar_process_discovery.discovery.proseqo.greedy_cover import compute_cover
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score
from prolothar_process_discovery.discovery.proseqo.mdl_score import estimate_lower_bound_mdl_score

class CandidateEvaluationWorker(Process):
    """
    A subprocess that evaluates operations on a pattern-dfg by computing
    the MDL gain.
    """
    def __init__(self, original_dfg: PatternDfg, log: EventLog,
                 result_queue: Queue,
                 use_estimated_mdl_for_candidate_generation: bool):
        super().__init__()
        self.__parameter_queue = Queue()
        self.__parameter_queue.put(original_dfg)
        self.__parameter_queue.put(log)
        self.__parameter_queue.put(use_estimated_mdl_for_candidate_generation)
        self.__result_queue = result_queue

    def run(self):
        original_dfg = self.__parameter_queue.get()
        log = self.__parameter_queue.get()
        use_estimated_mdl = self.__parameter_queue.get()

        while True:
            try:
                new_candidates, mdl_of_folded_dfg, selected_candidates = \
                    self.__parameter_queue.get()

                _evaluate_new_candidates(
                        original_dfg, log, selected_candidates, new_candidates,
                        mdl_of_folded_dfg, self.__result_queue, use_estimated_mdl)
            except Exception as e:
                self.__result_queue.put((e, None))

    def evaluate_candidates(
            self, new_candidates_partition: List[Candidate],
            mdl_of_folded_dfg: float,
            selected_candidates: List[Candidate]):
        self.__parameter_queue.put((
                new_candidates_partition, mdl_of_folded_dfg,
                selected_candidates))

class SingleThreadCandidateEvaluationWorker():
    """non-process version of CandidateEvaluationWorker"""
    def __init__(self, original_dfg: PatternDfg, log: EventLog,
                 result_queue: Queue,
                 use_estimated_mdl_for_candidate_generation: bool):
        super().__init__()
        self.__result_queue = result_queue
        self.__original_dfg = original_dfg
        self.__log = log
        self.__use_estimated_mdl = use_estimated_mdl_for_candidate_generation

    def evaluate_candidates(
            self, new_candidates_partition: List[Candidate],
            mdl_of_folded_dfg: float,
            selected_candidates: List[Candidate]):

        _evaluate_new_candidates(
                self.__original_dfg, self.__log, selected_candidates,
                new_candidates_partition, mdl_of_folded_dfg, self.__result_queue,
                self.__use_estimated_mdl)

    def terminate(self):
        pass

    def join(self):
        pass

def _evaluate_new_candidates(
        original_dfg: PatternDfg, log: EventLog,
        selected_candidates: List[Candidate], new_candidates: List[Candidate],
        mdl_of_folded_dfg: float, result_queue: Queue, use_estimated_mdl: bool):
    if use_estimated_mdl:
        pattern_dfg_without_new_candidate = original_dfg.copy()
        for candidate in selected_candidates:
            candidate.apply_on_dfg(pattern_dfg_without_new_candidate)
        cover_without_new_candidate = compute_cover(
                log.traces, pattern_dfg_without_new_candidate)
        for new_candidate in new_candidates:
            mdl_gain = mdl_of_folded_dfg - estimate_lower_bound_mdl_score(
                    pattern_dfg_without_new_candidate,
                    cover_without_new_candidate,
                    new_candidate, log, original_dfg)

            if mdl_gain > 0:
                    result_queue.put((mdl_gain, new_candidate))
    else:
        activity_set = log.compute_activity_set()
        for new_candidate in new_candidates:
            mdl_gain = _compute_exact_mdl_gain(
                    original_dfg, log, selected_candidates,
                    new_candidate, mdl_of_folded_dfg,
                    activity_set)

            if mdl_gain > 0:
                result_queue.put((mdl_gain, new_candidate))
    #signal that new_candidates is processed
    result_queue.put(None)

def _compute_exact_mdl_gain(
        dfg: PatternDfg, log: EventLog, selected_candidates: List[Candidate],
        new_candidate: Candidate, current_mdl: float,
        activity_set: set) -> float:
    try:
        candidate_dfg, _ = apply_candidate(dfg, selected_candidates, new_candidate)
        return current_mdl - compute_mdl_score(log, candidate_dfg, activity_set=activity_set)
    except KeyError as e:
        with open('temp.txt', 'w') as f:
            f.write('===============\n')
            for c in selected_candidates:
                f.write(str(c) + '\n')
            f.write('----------------\n')
            f.write(str(new_candidate) + '\n')
            f.write('----------------\n')
            for c in merge_candidates(
                    selected_candidates, [new_candidate]):
                f.write(str(c) + '\n')
            f.write('===============\n')
        pdfg = dfg.copy()
        for c in selected_candidates:
            c.apply_on_dfg(pdfg)
        pdfg.plot(filepath='temp')
        raise e
