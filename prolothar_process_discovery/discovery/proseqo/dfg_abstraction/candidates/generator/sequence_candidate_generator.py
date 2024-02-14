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

from typing import Iterable

from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.sequence_candidates import find_sequence_candidates_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import find_isolated_sequences_in_dfg

class SequenceCandidateGenerator(PatternCandidateGenerator):
    """generates sequence pattern candidates from a pattern_dfg"""

    def __init__(self, only_perfect_matches: bool = False,
                 keep_degeneration: bool = False):
        super().__init__(keep_degeneration=keep_degeneration)
        self.__only_perfect_matches = only_perfect_matches

    def _generate_patterns(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Candidate]:
        if self.__only_perfect_matches:
            return find_isolated_sequences_in_dfg(pattern_dfg)
        else:
            return find_sequence_candidates_in_dfg(pattern_dfg)
