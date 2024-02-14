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
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.composite import CandidateComposite

from typing import Set

class WeightedEdgeRemovalCandidateGenerator(CandidateGenerator):
    """generates EdgeRemovalCandidates. a group of edges is added as
    candidates if they belong to the same node and their weights are less
    than a certain percentage of the maximal weighted edge
    """

    def __init__(self, minimal_local_weight_in_percent: float,
                 post_generator: CandidateGenerator = None):
        if not (0 < minimal_local_weight_in_percent < 1):
            raise ValueError('minimal_local_weight_in_percent must be in (0,1)')
        self.__minimal_local_weight_in_percent = minimal_local_weight_in_percent
        self.__post_generator = post_generator

    def generate_candidates(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Set[Candidate]:
        candidates = set()
        edges_to_remove = set()
        if self.__post_generator is not None:
            candidates_before_removal = \
                self.__post_generator.generate_candidates(
                    log, pattern_dfg)
        for node in pattern_dfg.get_nodes():
            maximal_edge_weight = self.__get_maximal_edge_weight(node)

            edges_for_removal = self.__find_edges_for_removal(
                    node, maximal_edge_weight)

            if edges_for_removal:
                candidates.add(CandidateEdgeRemoval(edges_for_removal))
                if self.__post_generator is not None:
                    for edge in edges_for_removal:
                        pattern_dfg.remove_edge((edge.start.activity,
                                                 edge.end.activity))
                    for candidate_pattern in self.__post_generator.generate_candidates(
                            log, pattern_dfg).difference(
                                candidates_before_removal):
                        candidates.add(CandidateComposite([
                            CandidateEdgeRemoval(edges_for_removal),
                            candidate_pattern]))
                    for edge in edges_for_removal:
                        pattern_dfg.add_count(
                            edge.start.activity, edge.end.activity,
                            count=edge.count)

            edges_to_remove.update(edges_for_removal)

        return candidates

    def __find_edges_for_removal(self, node, maximal_edge_weight):
        edges_for_removal = []
        for edge in node.edges:
            if (edge.count / maximal_edge_weight
                ) < self.__minimal_local_weight_in_percent:
                edges_for_removal.append(edge)
        return edges_for_removal

    def __get_maximal_edge_weight(self, node) -> int:
        maximal_edge_weight = 0
        for edge in node.edges:
            if edge.count > maximal_edge_weight:
                maximal_edge_weight = edge.count
        return maximal_edge_weight