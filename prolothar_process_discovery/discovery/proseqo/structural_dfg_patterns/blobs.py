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

from prolothar_process_discovery.discovery.proseqo.pattern.blob import Blob
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.cliques import find_cliques_of_size_2
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.cliques import merge_2_cliques

from typing import Set

def find_binary_blob_candidates_in_dfg(dfg: PatternDfg) -> Set[Blob]:
    """returns all two-cliques in the DFG as blob candidates"""
    blob_candidates = set()

    for clique in find_cliques_of_size_2(dfg):
        node_1 = dfg.nodes[clique[0]]
        node_2 = dfg.nodes[clique[1]]

        blob_candidates.add(Blob(
            node_1.pattern.get_activity_set().union(
                node_2.pattern.get_activity_set())))

    return blob_candidates

def find_blob_candidates_in_dfg(dfg: PatternDfg) -> Set[Blob]:
    """returns chain of cliques in the DFG as blob candidates. If a and b is
    a clique, and b and c is clique, then a,b,c is returned as a blob candidate
    """
    blob_candidates = set()

    for clique in merge_2_cliques(find_cliques_of_size_2(dfg)):
        blob_activities = set()
        for activity in clique:
            blob_activities.update(dfg.nodes[activity].pattern.get_activity_set())
        blob_candidates.add(Blob(blob_activities))

    return blob_candidates