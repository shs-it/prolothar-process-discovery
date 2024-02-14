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

from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_optionals import find_one_step_optionals_in_dfg

class OptionalCandidateGenerator(PatternCandidateGenerator):
    """finds optional pattern candidates including induced sequences in a
    pattern_dfg
    """

    def __init__(self, keep_degeneration: bool = False,
                 induce_sequences: bool = True,
                 only_perfect_matches=True):
        super().__init__(keep_degeneration=keep_degeneration)
        self.__induce_sequences = induce_sequences
        self.__only_perfect_matches = only_perfect_matches

    def _generate_patterns(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Candidate]:
        return find_one_step_optionals_in_dfg(
                pattern_dfg, find_induced_sequences = self.__induce_sequences,
                only_perfect_matches = self.__only_perfect_matches)
