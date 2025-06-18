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

from typing import Iterable

from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.blobs import find_blob_candidates_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.blobs import find_binary_blob_candidates_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import return_induced_sequence_if_existing
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_choices import find_one_step_choice_from_branch_candidate_node

class BlobCandidateGenerator(PatternCandidateGenerator):
    """finds blob pattern candidates in a pattern_dfg"""

    def _generate_patterns(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Candidate]:
        candidates = find_binary_blob_candidates_in_dfg(pattern_dfg)
        candidates.update(find_blob_candidates_in_dfg(pattern_dfg))

        for candidate in list(candidates):
            try:
                candidate_dfg = pattern_dfg.fold({candidate})
                induced_choice = find_one_step_choice_from_branch_candidate_node(
                        candidate_dfg, candidate_dfg.nodes[candidate.get_activity_name()])
                if induced_choice is not None:
                    candidates.add(induced_choice)
            except KeyError:
                #if the  blob was created with a subpattern, then we cannot
                #fold the graph.
                pass

        for candidate in list(candidates):
            try:
                candidates.add(return_induced_sequence_if_existing(
                        candidate, pattern_dfg))
            except KeyError:
                #if the  blob was created with a subpattern, then we cannot
                #fold the graph.
                pass

        return candidates

