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
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.pattern_candidate_generator import PatternCandidateGenerator

from typing import Iterable

class Deoptionalizer(PatternCandidateGenerator):
    """finds existing patterns that have an optional as subpattern
    and generates candidates of these patterns without the optional part. if a
    pattern has more than one optional as subpattern, than there is candidate
    for each optional individually, i.e. if [a?,b?] is the pattern, then
    [a,b?] and [b?,a] are generated
    """

    def __init__(self, keep_degeneration: bool = False):
        super().__init__(keep_degeneration=keep_degeneration)

    def _generate_patterns(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Candidate]:
        candidates = []

        for node in pattern_dfg.get_nodes():
            candidates.extend(self.__generate_candidates_from_pattern(
                    node.pattern))

        return candidates

    def __generate_candidates_from_pattern(
            self, pattern: Pattern):
        if pattern.is_optional():
            yield pattern.opt_pattern
        for subpattern in pattern.get_subpatterns():
            for new_subpattern in self.__generate_candidates_from_pattern(
                    subpattern):
                new_pattern = pattern.copy()
                new_pattern.replace_direct_subpattern(subpattern, new_subpattern)
                yield new_pattern

