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
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.candidate_generator import CandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.union_candidate_generator import UnionCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.sequence_candidate_generator import SequenceCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.choice_candidate_generator import ChoiceCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.optional_candidate_generator import OptionalCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.loop_candidate_generator import LoopCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.parallel_candidate_generator import ParallelCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.blob_candidate_generator import BlobCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.edge_removal_candidate_generator import EdgeRemovalCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.weighted_edge_removal_candidate_generator import WeightedEdgeRemovalCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.node_removal_candidate_generator import NodeRemovalCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.noisy_sequence_candidate_generator import NoisySequenceCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.one_pattern_candidate_generator import OnePatternCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.perfect_matching_candidate_generator import PerfectMatchingCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.parallel_to_sequence_generator import ParallelToSequenceGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.deoptionalizer import Deoptionalizer
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.brutal_edge_pruning_pattern_generator import BrutalEdgePruningPatternGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.anti_swap_noise_edge_removal_generator import AntiSwapNoiseEdgeRemovalCandidateGenerator

from typing import Set

class CandidateGeneratorBuilder():
    """gives the possibility to create a union of candidate generators without
    the need to import them all manually
    """

    def __init__(self):
        self.__generators = []

    def with_choices(
            self, only_perfect_matches: bool = False,
            keep_degeneration: bool = False,
            force_binary_choices_creation = True,
            induce_sequences = True,
            no_choice_activities: Set[str] = None) -> 'CandidateGeneratorBuilder':
        """choices will be included in the candidate generation"""
        self.__generators.append(ChoiceCandidateGenerator(
                only_perfect_matches=only_perfect_matches,
                keep_degeneration=keep_degeneration,
                force_binary_choices_creation=force_binary_choices_creation,
                induce_sequences=induce_sequences,
                no_choice_activities=no_choice_activities))
        return self

    def with_sequences(
            self, only_perfect_matches: bool = False,
            keep_degeneration: bool = False) -> 'CandidateGeneratorBuilder':
        """sequences will be included in the candidate generation"""
        self.__generators.append(SequenceCandidateGenerator(
                only_perfect_matches=only_perfect_matches,
                keep_degeneration=keep_degeneration))
        return self

    def with_noisy_sequences(self) -> 'CandidateGeneratorBuilder':
        """sequences with noise sets will be included in the candidate generation"""
        self.__generators.append(NoisySequenceCandidateGenerator())
        return self

    def with_optionals(
            self, keep_degeneration: bool = False,
            induce_sequences: bool = True,
            only_perfect_matches: bool = False) -> 'CandidateGeneratorBuilder':
        """optionals will be included in the candidate generation"""
        self.__generators.append(OptionalCandidateGenerator(
                keep_degeneration=keep_degeneration,
                induce_sequences=induce_sequences,
                only_perfect_matches=only_perfect_matches))
        return self

    def with_loops(
            self, find_induced_sequences: bool = True,
            keep_degeneration: bool = False,
            only_perfect_matches: bool = False) -> 'CandidateGeneratorBuilder':
        """loops will be included in the candidate generation"""
        self.__generators.append(LoopCandidateGenerator(
                find_induced_sequences=find_induced_sequences,
                keep_degeneration=keep_degeneration,
                only_perfect_matches=only_perfect_matches))
        return self

    def with_parallels(
            self, only_perfect_matches: bool = False,
            keep_degeneration: bool = False) -> 'CandidateGeneratorBuilder':
        """parallels will be included in the candidate generation"""
        self.__generators.append(ParallelCandidateGenerator(
                only_perfect_matches=only_perfect_matches,
                keep_degeneration=keep_degeneration))
        return self

    def with_parallels_to_sequences(
            self, consider_subpatterns: bool = False,
            keep_degeneration: bool = False) -> 'CandidateGeneratorBuilder':
        """parallels will be turned into sequences in the candidate generation
        process
        """
        self.__generators.append(ParallelToSequenceGenerator(
                keep_degeneration=keep_degeneration,
                consider_subpatterns=consider_subpatterns))
        return self

    def with_deoptionalizer(
            self, only_perfect_matches: bool = False,
            keep_degeneration: bool = False) -> 'CandidateGeneratorBuilder':
        """optionals will be turned into their subpatterns as candidates
        """
        self.__generators.append(Deoptionalizer(
                keep_degeneration=keep_degeneration))
        return self

    def with_blobs(self) -> 'CandidateGeneratorBuilder':
        """Blobs will be included in the candidate generation"""
        self.__generators.append(BlobCandidateGenerator())
        return self

    def with_one_pattern_generator(self) -> 'CandidateGeneratorBuilder':
        """adds a generator that tries to compress the whole given pattern_dfg
        into one sequence
        """
        self.__generators.append(OnePatternCandidateGenerator())
        return self

    def with_perfect_matching_patterns_generator(self) -> 'CandidateGeneratorBuilder':
        """adds a generator that tries to compress the pattern_dfg with perfectly
        matching loops, choices, parallels, sequences, optionals
        """
        self.__generators.append(PerfectMatchingCandidateGenerator())
        return self

    def with_brutal_edge_pruning_pattern_generator(
            self, no_choice_activities: Set[str] = None) -> 'CandidateGeneratorBuilder':
        """adds a generator that tries to compress the pattern_dfg with perfectly
        matching loops, choices, parallels, sequences, optionals after
        pruning the graph with several frequency thresholds
        """
        self.__generators.append(BrutalEdgePruningPatternGenerator(
            no_choice_activities=no_choice_activities))
        return self

    def with_edge_removals(self) -> 'CandidateGeneratorBuilder':
        """EdgeRemovalCandidates will be included in the candidate generation"""
        self.__generators.append(EdgeRemovalCandidateGenerator())
        return self

    def with_weighted_edge_removals(
            self, minimal_local_weight_in_percent: float,
            post_generator: CandidateGenerator = None) -> 'CandidateGeneratorBuilder':
        self.__generators.append(WeightedEdgeRemovalCandidateGenerator(
                minimal_local_weight_in_percent,
                post_generator = post_generator))
        return self

    def with_anti_swap_edge_removals(
            self, threshold: float) -> 'CandidateGeneratorBuilder':
        self.__generators.append(AntiSwapNoiseEdgeRemovalCandidateGenerator(
            threshold))
        return self

    def with_node_removals(
            self, protected_activities: Set[str] = None) -> 'CandidateGeneratorBuilder':
        """NodeRemovalCandidates will be included in the candidate generation"""
        self.__generators.append(NodeRemovalCandidateGenerator(
                protected_activities=protected_activities))
        return self

    def with_generator(
            self, generator: CandidateGenerator) -> 'CandidateGeneratorBuilder':
        """
        Adds the given CandidateGenerator to the list of generators
        """
        self.__generators.append(generator)
        return self

    def build(self) -> CandidateGenerator:
        """creates a new candidate generator with the settings of this builder
        """
        return UnionCandidateGenerator(self.__generators)
