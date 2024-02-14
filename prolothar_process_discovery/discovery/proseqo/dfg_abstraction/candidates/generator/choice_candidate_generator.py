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
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.pattern_candidate_generator import PatternCandidateGenerator

from typing import Iterable, Set

from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.choice_candidates import find_choice_candidates_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.binary_choice_candidates import find_binary_choice_candidates_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_choices import find_one_step_choices_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import return_induced_sequence_if_existing

class ChoiceCandidateGenerator(PatternCandidateGenerator):
    """finds choice pattern candidates in a pattern_dfg"""

    def __init__(self, only_perfect_matches: bool = False,
                 keep_degeneration: bool = False,
                 force_binary_choices_creation = True,
                 no_choice_activities: Set[str] = None,
                 induce_sequences: bool = True):
        super().__init__(keep_degeneration=keep_degeneration)
        self.__only_perfect_matches = only_perfect_matches
        self.__force_binary_choices_creation = force_binary_choices_creation
        if no_choice_activities is not None:
            self.__no_choice_activities = no_choice_activities
        else:
            self.__no_choice_activities = set()
        self.__induce_sequences = induce_sequences

    def _generate_patterns(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Pattern]:
        if self.__only_perfect_matches:
            candidates = find_one_step_choices_in_dfg(pattern_dfg)
            if self.__induce_sequences:
                candidates = [return_induced_sequence_if_existing(c, pattern_dfg)
                              for c in candidates]
        else:
            if self.__force_binary_choices_creation:
                candidates = find_binary_choice_candidates_in_dfg(pattern_dfg)
            else:
                candidates = set()
            candidates.update(find_choice_candidates_in_dfg(pattern_dfg))
            if self.__induce_sequences:
                for candidate in find_one_step_choices_in_dfg(pattern_dfg):
                    candidates.discard(candidate)
                    candidates.add(return_induced_sequence_if_existing(
                        candidate, pattern_dfg))

        if self.__no_choice_activities:
            candidates = [c for c in candidates
                          if not c.get_activity_set().intersection(
                                  self.__no_choice_activities)]

        return candidates