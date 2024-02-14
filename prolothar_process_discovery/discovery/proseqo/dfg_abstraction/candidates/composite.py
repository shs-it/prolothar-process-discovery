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

import prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidate as candidate

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.cover import Cover

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

from typing import Dict, List, Tuple

class CandidateComposite(candidate.Candidate):
    """container for multiple candidates that should be applied together"""
    def __init__(self, candidates: List[candidate.Candidate]):
        super().__init__()
        self.__candidates = tuple(candidates)

    def __repr__(self) -> str:
        return 'composite: %s' % str(self.__candidates)

    def apply_on_dfg(self, dfg: PatternDfg):
        for c in self.__candidates:
            c.apply_on_dfg(dfg)

    def __hash__(self) -> int:
        return hash(self.__candidates)

    def __eq__(self, other) -> int:
        try:
            return self.__candidates == other.__candidates
        except AttributeError:
            return False

    def _has_conflict_with_candidate_pattern(self, other) -> bool:
        raise ValueError('should not add composite to selected candidate list')

    def _has_conflict_with_candidate_edge_removal(self, other) -> bool:
        raise ValueError('should not add composite to selected candidate list')

    def _has_conflict_with_candidate_node_removal(self, other) -> bool:
        raise ValueError('should not add composite to selected candidate list')

    def get_sort_type_int(self) -> int:
        raise ValueError('should not add composite to selected candidate list')

    def estimate_cover_change(
            self, cover: Cover, pattern_dfg_before_candidate: PatternDfg,
            dfg: DirectlyFollowsGraph) -> PatternDfg:
        pattern_dfg = pattern_dfg_before_candidate
        for c in self.__candidates:
            pattern_dfg = c.estimate_cover_change(cover, pattern_dfg, dfg)
        return pattern_dfg

    def get_candidates(self) -> Tuple[candidate.Candidate]:
        return self.__candidates

    def is_composite(self):
        return True

    def get_frequency_priority(self, activity_supports: Dict[str, int]) -> tuple[int]:
        """we return the minimal frequency priority of the subcandidates"""
        return min(c.get_frequency_priority(activity_supports)
                   for c in self.__candidates)