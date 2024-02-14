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
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import CandidateEdgeRemoval

from typing import Set

class EdgeRemovalCandidateGenerator(CandidateGenerator):
    """generates EdgeRemovalCandidates. every single edge is added as a
    candidate
    """

    def generate_candidates(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Set[Candidate]:
        sources_connected_by_single_edge = set(
            node.activity for node in pattern_dfg.get_source_nodes()
            if len(node.edges) == 1)
        sinks_connected_by_single_edge = set(
            node.activity for node in pattern_dfg.get_sink_nodes()
            if len(node.ingoing_edges) == 1)
        return set(
                CandidateEdgeRemoval([edge])
                for edge in pattern_dfg.edges.values()
                if edge.start.activity not in sources_connected_by_single_edge
                and edge.end.activity not in sinks_connected_by_single_edge)
