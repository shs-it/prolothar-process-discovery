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
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import CandidateNodeRemoval

from typing import Set

class NodeRemovalCandidateGenerator(CandidateGenerator):
    """generates NodeRemovalCandidates"""

    def __init__(self, protected_activities: Set[str] = None):
        """
        Args:
            protected_activities:
                a set with activities that are not allowed to be removed
        """
        if protected_activities is not None:
            self.__protected_activities = protected_activities
        else:
            self.__protected_activities = {'START', 'Start', 'END', 'End'}

    def generate_candidates(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Set[Candidate]:
        return set(CandidateNodeRemoval(node.pattern)
                   for node in pattern_dfg.get_nodes()
                   if self.__is_allowed_to_remove_node(node))

    def __is_allowed_to_remove_node(self, node) -> bool:
        for protected_activity in self.__protected_activities:
            if node.pattern.contains_activity(protected_activity):
                return False
        return True
