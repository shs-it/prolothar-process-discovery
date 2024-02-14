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
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.cliques import find_cliques_of_size_2

from typing import Set

class AntiSwapNoiseEdgeRemovalCandidateGenerator(CandidateGenerator):
    """generates EdgeRemovalCandidates. the less frequent edges of 2-cliques
    are removed if their relative frequency is below a threshold
    """

    def __init__(self, threshold: float):
        self.__threshold = threshold

    def generate_candidates(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Set[Candidate]:
        edges_for_removal = []
        for clique in find_cliques_of_size_2(pattern_dfg):
            edge = pattern_dfg.edges[clique]
            anti_edge = pattern_dfg.edges[clique[::-1]]
            if edge.count < anti_edge.count:
                edge,anti_edge = anti_edge,edge
            if edge.count > 0 and anti_edge.count / edge.count < self.__threshold:
                edges_for_removal.append(anti_edge)
        if edges_for_removal:
            candidates = set([CandidateEdgeRemoval(edges_for_removal)])
        else:
            candidates = set()

        edges_from_source = []
        for source in pattern_dfg.get_source_nodes():
            edges_from_source.append(set(source.edges))
        edges_to_sink = []
        for sink in pattern_dfg.get_sink_nodes():
            edges_to_sink.append(set(sink.ingoing_edges))

        all_obsolete_ingoing_edges = set()
        all_obsolete_outgoing_edges = set()
        for node in pattern_dfg.get_nodes():
            max_outgoing_count = 0
            for edge in node.edges:
                if edge.count > max_outgoing_count:
                    max_outgoing_count = edge.count
            max_ingoing_count = 0
            for edge in node.ingoing_edges:
                if edge.count > max_ingoing_count:
                    max_ingoing_count = edge.count

            obsolete_outgoing_edges = [
                edge for edge in node.edges
                if max_outgoing_count > 0 and edge.count / max_outgoing_count < self.__threshold]
            obsolete_ingoing_edges = [
                edge for edge in node.ingoing_edges
                if max_ingoing_count > 0 and edge.count / max_ingoing_count < self.__threshold]

            does_not_cut_a_sink = all(a.difference(obsolete_outgoing_edges)
                                      for a in edges_to_sink)
            does_not_cut_a_source = all(a.difference(obsolete_ingoing_edges)
                                      for a in edges_from_source)
            if obsolete_outgoing_edges and does_not_cut_a_sink:
                candidates.add(CandidateEdgeRemoval(obsolete_outgoing_edges))
            if obsolete_ingoing_edges and does_not_cut_a_source:
                candidates.add(CandidateEdgeRemoval(obsolete_ingoing_edges))
            if obsolete_outgoing_edges and obsolete_ingoing_edges \
            and does_not_cut_a_source and does_not_cut_a_sink:
                candidates.add(CandidateEdgeRemoval(
                    obsolete_ingoing_edges + obsolete_outgoing_edges))

            all_obsolete_ingoing_edges.update(obsolete_ingoing_edges)
            all_obsolete_outgoing_edges.update(obsolete_outgoing_edges)

        does_not_cut_a_sink = all(a.difference(all_obsolete_outgoing_edges)
                                  for a in edges_to_sink)
        does_not_cut_a_source = all(a.difference(all_obsolete_ingoing_edges)
                                    for a in edges_from_source)
        if all_obsolete_outgoing_edges and does_not_cut_a_sink:
            candidates.add(CandidateEdgeRemoval(all_obsolete_outgoing_edges))
        if all_obsolete_ingoing_edges and does_not_cut_a_source:
            candidates.add(CandidateEdgeRemoval(all_obsolete_ingoing_edges))
        if all_obsolete_outgoing_edges and all_obsolete_ingoing_edges \
        and does_not_cut_a_source and does_not_cut_a_sink:
            candidates.add(CandidateEdgeRemoval(
                all_obsolete_ingoing_edges.union(all_obsolete_outgoing_edges)))

        last_min_count_edges = []
        remaining_edges = pattern_dfg.get_edges()
        while remaining_edges:
            next_remaining_edges = []
            min_count_edges = []
            min_count = float('inf')
            for edge in remaining_edges:
                if edge.count < min_count:
                    next_remaining_edges.extend(min_count_edges)
                    min_count_edges = [edge]
                    min_count = edge.count
                elif edge.count > min_count:
                    next_remaining_edges.append(edge)
                else:
                    min_count_edges.append(edge)
            does_not_cut_a_sink = all(a.difference(min_count_edges)
                                      for a in edges_to_sink)
            does_not_cut_a_source = all(a.difference(min_count_edges)
                                        for a in edges_from_source)
            if does_not_cut_a_sink and does_not_cut_a_source:
                last_min_count_edges.extend(min_count_edges)
                candidates.add(CandidateEdgeRemoval(last_min_count_edges))
                remaining_edges = next_remaining_edges
            else:
                remaining_edges = []

        return candidates
