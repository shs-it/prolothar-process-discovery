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

from datetime import datetime
from abc import ABC, abstractmethod

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

from typing import Tuple, Dict

class Candidate(ABC):
    def __init__(self):
        self.__timestamp = datetime.now()
    @abstractmethod
    def apply_on_dfg(self, dfg: PatternDfg):
        pass

    def has_conflict_with(self, other: 'Candidate') -> bool:
        import prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.pattern as apply_pattern
        import prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.edge_removal as edge_removal
        import prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.node_removal as node_removal
        if isinstance(other, apply_pattern.CandidatePattern):
            return self._has_conflict_with_candidate_pattern(other)
        elif isinstance(other, edge_removal.CandidateEdgeRemoval):
            return self._has_conflict_with_candidate_edge_removal(other)
        elif isinstance(other, node_removal.CandidateNodeRemoval):
            return self._has_conflict_with_candidate_node_removal(other)
        raise NotImplementedError()

    def get_timestamp(self):
        return self.__timestamp

    def __lt__(self, other) -> bool:
        #if two candidates have the same MDL gain, take the older one
        return self.__timestamp > other.__timestamp

    @abstractmethod
    def _has_conflict_with_candidate_pattern(self, other) -> bool:
        pass

    @abstractmethod
    def _has_conflict_with_candidate_edge_removal(self, other) -> bool:
        pass

    @abstractmethod
    def _has_conflict_with_candidate_node_removal(self, other) -> bool:
        pass

    @abstractmethod
    def get_sort_type_int(self) -> int:
        """returns a int as sort criteria which candidate type should be applied
        first"""

    def get_sort_tuple(self) -> Tuple:
        """returns a tuple as sort criteria which candidate should be applied
        first"""
        return (self.get_sort_type_int(), self.__timestamp)

    @abstractmethod
    def estimate_cover_change(
            self, cover, pattern_dfg_before_candidate: PatternDfg,
            dfg: DirectlyFollowsGraph) -> PatternDfg:
        """changes the given cover as an estimate how the cover will change for
        this candidate.

        Args:
            - pattern_dfg_before_candidate:
                can safely be changed

        Returns:
            pattern_dfg after candidate application
        """

    @abstractmethod
    def estimate_cover_change_for_lower_bound(
            self, cover, pattern_dfg_before_candidate: PatternDfg,
            dfg: DirectlyFollowsGraph) -> PatternDfg:
        """changes the given cover as an estimate how the cover will change for
        this candidate. the estimate gives a lower bound for L(D|M).

        Args:
            - pattern_dfg_before_candidate:
                can safely be changed

        Returns:
            pattern_dfg after candidate application
        """

    @abstractmethod
    def get_frequency_priority(self, activity_supports: Dict[str, int]) -> tuple[int]:
        """returns a (estimated) frequency rank of the candidate that is used to
        sort the candidates in a priority queue. e.g. less frequent edges are
        more probable to decrease the MDL than frequent edges
        """

    def is_composite(self):
        """returns True if this candidate is from type CandidateComposite"""
        return False