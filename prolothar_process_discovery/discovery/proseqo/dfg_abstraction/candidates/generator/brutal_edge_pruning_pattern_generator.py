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
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import Candidate
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.pattern_candidate_generator import PatternCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.perfect_matching_candidate_generator import PerfectMatchingCandidateGenerator

from typing import Iterable, List, Set

class BrutalEdgePruningPatternGenerator(PatternCandidateGenerator):
    """removes many edges by frequency filtering with different thresholds
    and generates patterns from the remaining graph
    """

    def __init__(self, keep_degeneration: bool = False,
                 frequencies: List[float] = None,
                 no_choice_activities: Set[str] = None,
                 parallels: bool = False):
        super().__init__(keep_degeneration=keep_degeneration)
        self.__candidate_generator = PerfectMatchingCandidateGenerator(
                keep_degeneration=keep_degeneration,
                no_choice_activities=no_choice_activities,
                parallels=parallels)
        if frequencies is not None:
            self.__frequencies = frequencies
        else:
            self.__frequencies = [0.05, 0.1, 0.2]

    def _generate_patterns(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Candidate]:
        candidates = set()

        for min_local_frequency in self.__frequencies:
            candidate_dfg = pattern_dfg.filter_edges_by_local_frequency(
                    min_local_frequency)
            for candidate in self.__candidate_generator.generate_candidates(
                    log, dfg, candidate_dfg):
                candidates.add(candidate.get_pattern())

        return candidates