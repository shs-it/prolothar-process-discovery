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

import psutil
import itertools

from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg

from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.dfg_abstraction_strategy import DfgAbstractionStrategy
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.union import Union

from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.candidate_generator_builder import CandidateGeneratorBuilder
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.iterative_best_pattern import IterativeBestPattern

class Proseqo(DfgAbstractionStrategy):
    """
    algorithm for our paper. this class is a facade to implemented stuff in
    this package. it uses the union strategy and the iterative best pattern
    strategy to mine processes with sequences, choices, loops, optionals
    that can include noise.
    """

    def __init__(
            self, max_nr_of_workers: int = psutil.cpu_count(),
            multiple_iterations: bool = False,
            use_mdl_estimates: bool = False,
            anti_swap_noise_candidate_generator: bool = True):
        self.__max_nr_of_workers = max_nr_of_workers
        self.__multiple_iterations = multiple_iterations
        self.__use_mdl_estimates = use_mdl_estimates
        self.__anti_swap_noise_candidate_generator = anti_swap_noise_candidate_generator

    def mine_dfg(self, log: EventLog, dfg: PatternDfg,
                 verbose: bool = False) -> PatternDfg:

        source_and_sink_aktivities = set()
        for node in itertools.chain(
                dfg.get_source_nodes(), dfg.get_sink_nodes()):
            source_and_sink_aktivities.update(node.pattern.get_activity_set())

        if self.__anti_swap_noise_candidate_generator:
            edge_candidate_generator = CandidateGeneratorBuilder()\
                                .with_edge_removals()\
                                .with_anti_swap_edge_removals(0.05)\
                                .with_anti_swap_edge_removals(0.1)\
                                .with_anti_swap_edge_removals(0.2)\
                                .with_anti_swap_edge_removals(0.3)\
                                .with_anti_swap_edge_removals(0.4)\
                                .with_anti_swap_edge_removals(0.5)\
                                .with_anti_swap_edge_removals(0.6)\
                                .build()
        else:
            edge_candidate_generator = CandidateGeneratorBuilder()\
                                .with_edge_removals()\
                                .build()
        #.with_one_pattern_generator()\
        candidate_generator = CandidateGeneratorBuilder()\
                            .with_generator(edge_candidate_generator)\
                            .with_brutal_edge_pruning_pattern_generator(
                                no_choice_activities=source_and_sink_aktivities)\
                            .with_choices(
                                no_choice_activities=source_and_sink_aktivities,
                                force_binary_choices_creation=True)\
                            .with_optionals()\
                            .with_deoptionalizer()\
                            .with_sequences()\
                            .with_loops()\
                            .with_node_removals(
                                protected_activities=source_and_sink_aktivities)\
                            .build()

        return Union([
            IterativeBestPattern(
                        edge_candidate_generator,
                        multiple_iterations=False,
                        candidate_pruning=True,
                        evaluation_limit='nodes',
                        apply_trivial_patterns=False,
                        use_estimated_mdl_for_candidate_generation=self.__use_mdl_estimates,
                        prune_with_lower_bound_estimates=(
                            not self.__use_mdl_estimates
                            and self.__max_nr_of_workers == 1),
                        max_nr_of_workers=self.__max_nr_of_workers),
            IterativeBestPattern(
                candidate_generator,
                candidate_pruning=True,
                evaluation_limit='nodes',
                max_nr_of_workers=self.__max_nr_of_workers,
                multiple_iterations=self.__multiple_iterations,
                use_estimated_mdl_for_candidate_generation=self.__use_mdl_estimates,
                prune_with_lower_bound_estimates=(
                    not self.__use_mdl_estimates
                    and self.__max_nr_of_workers == 1),
                apply_trivial_patterns=False)
        ]).mine_dfg(log, dfg, verbose=verbose)

    def __repr__(self) -> str:
        return 'Proseqo(max_nr_of_workers=%d)' % self.__max_nr_of_workers
