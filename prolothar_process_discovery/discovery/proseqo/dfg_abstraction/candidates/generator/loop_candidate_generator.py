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
from prolothar_process_discovery.discovery.proseqo.pattern.loop import Loop
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.pattern_candidate_generator import PatternCandidateGenerator

from typing import Iterable

from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_loops import find_isolated_loops_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.two_part_loop_candidates import find_two_part_loop_candidates_in_dfg

class LoopCandidateGenerator(PatternCandidateGenerator):
    """finds loop pattern candidates in a pattern_dfg"""

    def __init__(self, find_induced_sequences: bool = True,
                 keep_degeneration: bool = False,
                 only_perfect_matches: bool = False):
        super().__init__(keep_degeneration=keep_degeneration)
        self.__find_induced_sequences = find_induced_sequences
        self.__only_perfect_matches = only_perfect_matches

    def _generate_patterns(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Pattern]:
        candidates = set(find_isolated_loops_in_dfg(
                pattern_dfg, find_induced_sequences=self.__find_induced_sequences))
        if not self.__only_perfect_matches:
            candidates.update(find_two_part_loop_candidates_in_dfg(pattern_dfg))
            candidates.update(
                self.__generate_two_part_loops_candidates_from_removed_activities(
                    dfg, pattern_dfg))
        return candidates

    def __generate_two_part_loops_candidates_from_removed_activities(
            self, dfg: PatternDfg, pattern_dfg: PatternDfg) -> Iterable[Pattern]:

        candidates = []

        candidate_nodes = [node for node in pattern_dfg.get_nodes()
                           if node.pattern.is_singleton()
                           and node.is_followed_by(node.activity)]

        activities_in_pattern_dfg = set()
        for node in pattern_dfg.get_nodes():
            activities_in_pattern_dfg.update(node.pattern.get_activity_set())
        removed_activities = set(dfg.nodes.keys()).difference(
            activities_in_pattern_dfg)

        for node in candidate_nodes:
            for activity in removed_activities:
                if (node.activity, activity) in dfg.edges:
                    candidates.append(Loop(Sequence([
                        node.pattern, Optional(Singleton(activity))])))

        return candidates
