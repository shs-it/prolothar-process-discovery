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

from typing import List, Tuple

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg

from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidate import Candidate
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.pattern import CandidatePattern
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.edge_removal import CandidateEdgeRemoval
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.node_removal import CandidateNodeRemoval

def apply_candidate(
        original_dfg: PatternDfg, selected_candidates: List[Candidate],
        current_candidate: Candidate) -> Tuple[PatternDfg, List[Candidate]]:
    """applies the given candidate and all non-conflicting existing cadidates.
    Ensures the correct order of the candidates.
    """
    if current_candidate.is_composite():
        candidate_set = merge_candidates(
            selected_candidates, current_candidate.get_candidates())
    else:
        candidate_set = merge_candidates(selected_candidates, [current_candidate])
    candidate_dfg = original_dfg.copy()
    for candidate in candidate_set:
        candidate.apply_on_dfg(candidate_dfg)
    return candidate_dfg, candidate_set

def merge_candidates(candidate_list: List[Candidate],
                     additional_candidates: List[Candidate]) -> List[Candidate]:
    """merges candidate_list and additional_candidates such that there are no
    conflicts. the method also ensures the correct order of the candidates
    """
    merged_candidates = []
    for candidate in candidate_list:
        for additional_candidate in additional_candidates:
            if additional_candidate.has_conflict_with(candidate):
                break
        else:
            merged_candidates.append(candidate)
    merged_candidates += additional_candidates
    merged_candidates.sort(key=lambda c: c.get_sort_tuple())
    return merged_candidates

def infer_candidates(dfg: PatternDfg, pattern_dfg: PatternDfg) -> List[Candidate]:
    inferred_candidates = []
    expanded_dfg = pattern_dfg.expand()

    for edge in dfg.get_edges():
        if not (edge.start.activity,edge.end.activity) in expanded_dfg.edges:
            inferred_candidates.append(CandidateEdgeRemoval([edge]))

    for node in dfg.get_nodes():
        if not node.activity in expanded_dfg.nodes:
            inferred_candidates.append(CandidateNodeRemoval(node.pattern))

    for node in pattern_dfg.get_nodes():
        if not node.pattern.is_singleton():
            inferred_candidates.append(CandidatePattern(node.pattern))

    return inferred_candidates