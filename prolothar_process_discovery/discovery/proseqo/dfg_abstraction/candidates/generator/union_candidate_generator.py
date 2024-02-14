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
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.candidate_generator import CandidateGenerator

from typing import Set, List

class UnionCandidateGenerator(CandidateGenerator):
    """a candidate generations that uses a list of other candidate generators.
    multiple candidate generators can be combined with this class
    """

    def __init__(self, generators: List[CandidateGenerator]):
        if not generators:
            raise ValueError('generators must not be empty')
        self.__generators = generators

    def generate_candidates(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Set[Candidate]:
        generator_iterator = iter(self.__generators)
        generator = next(generator_iterator)
        candidates = generator.generate_candidates(log, dfg, pattern_dfg)
        while True:
            try:
                generator = next(generator_iterator)
                candidates.update(generator.generate_candidates(
                    log, dfg, pattern_dfg))
            except StopIteration:
                break
        return candidates

    def __repr__(self) -> str:
        return 'UnionCandidateGenerator(%r)' % self.__generators
