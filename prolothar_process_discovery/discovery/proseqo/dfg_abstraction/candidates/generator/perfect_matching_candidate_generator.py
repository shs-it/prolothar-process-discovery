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
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.union_candidate_generator import UnionCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.sequence_candidate_generator import SequenceCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.choice_candidate_generator import ChoiceCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.parallel_candidate_generator import ParallelCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.loop_candidate_generator import LoopCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.optional_candidate_generator import OptionalCandidateGenerator

from typing import Iterable, Set

class PerfectMatchingCandidateGenerator(PatternCandidateGenerator):
    """generates perfectly matching sequence, optional, parallel, choice and
    loop patterns. perfectly matching means the patterns correspond in a unique
    way to the structure of the given pattern_dfg, i.e. noise is being included
    """

    def __init__(self, keep_degeneration: bool = False,
                 no_choice_activities: Set[str] = None,
                 parallels: bool = True):
        super().__init__(keep_degeneration=keep_degeneration)

        candidate_generators = []
        candidate_generators.append(SequenceCandidateGenerator(
            only_perfect_matches=True, keep_degeneration=True))
        candidate_generators.append(ChoiceCandidateGenerator(
                    only_perfect_matches=True, keep_degeneration=True,
                    no_choice_activities=no_choice_activities))
        if parallels:
            candidate_generators.append(ParallelCandidateGenerator(
                only_perfect_matches=True, keep_degeneration=True))
        candidate_generators.append(LoopCandidateGenerator(
            only_perfect_matches=True, keep_degeneration=True,
            find_induced_sequences=False))
        candidate_generators.append(OptionalCandidateGenerator(
            only_perfect_matches=True, keep_degeneration=True,
            induce_sequences=False))

        self.__candidate_generator = UnionCandidateGenerator(candidate_generators)

    def _generate_patterns(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Candidate]:

        candidate_dfg = pattern_dfg.copy()

        while True:
            patterns = list(self.__candidate_generator.generate_candidates(
                None, dfg, candidate_dfg))
            changed = False
            for pattern in patterns:
                next_candidate_dfg = candidate_dfg.copy()
                try:
                    pattern.apply_on_dfg(next_candidate_dfg)
                    candidate_dfg = next_candidate_dfg
                    changed = True
                except KeyError:
                    #loop patterns can also include sequences, but these
                    #sequences without loop can also be in the patterns set.
                    #optionals can destroy structure for other patterns
                    #example: a and b are optional and siblings.
                    #a? and b? are in patterns as well as (a|b) can be applied.
                    #if the optionals are applied first, the choice is not
                    #applicable anymore and vice versa. the choice (a?|b?) will
                    #be found in the next iteration
                    pass
            if not patterns or not changed:
                break

        return [node.pattern for node in candidate_dfg.get_nodes()
                if node.pattern.get_activity_name() not in pattern_dfg.nodes]
