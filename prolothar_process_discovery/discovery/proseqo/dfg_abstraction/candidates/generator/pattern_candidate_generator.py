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
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import Candidate
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import CandidatePattern
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.candidate_generator import CandidateGenerator

from typing import Iterable

class PatternCandidateGenerator(CandidateGenerator):
    """finds pattern candidates in a pattern_dfg"""

    def __init__(self, keep_degeneration: bool = False):
        self.__keep_degeneration = keep_degeneration

    def generate_candidates(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Candidate]:
        candidates = set()
        for pattern in self._generate_patterns(log, dfg, pattern_dfg):
            if not self.__keep_degeneration:
                pattern = pattern.without_degeneration()[0]
                pattern.merge_subpatterns()
            candidates.add(CandidatePattern(pattern))
        return candidates

    def _generate_patterns(self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Pattern]:
        pass