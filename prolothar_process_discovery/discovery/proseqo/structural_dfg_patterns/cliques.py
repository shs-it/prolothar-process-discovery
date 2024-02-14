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

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from typing import Tuple, List, Set
from collections import deque

def find_cliques_of_size_2(dfg: DirectlyFollowsGraph) -> List[Tuple[str,str]]:
    """finds and returns all cliques of size 2"""
    cliques = []
    for i,node_i in enumerate(dfg.get_nodes()):
        for j,node_j in enumerate(dfg.get_nodes()):
            if (i < j and
                node_j.activity in dfg.get_following_activities(node_i.activity) and
                node_i.activity in dfg.get_following_activities(node_j.activity)):
                cliques.append((node_i.activity, node_j.activity))

    return cliques

def merge_2_cliques(cliques: List[Tuple[str,str]]) -> List[Set[str]]:
    """merges overlapping two-cliques. if a,b is a clique and b,c is clique,
    then a,b,c will be returned as a set
    """
    merged_cliques = []
    cliques = deque(cliques)
    while cliques:
        clique = cliques.pop()
        merged_clique = set(a for a in clique)
        for _ in range(len(cliques)):
            other_clique = cliques.pop()
            if other_clique[0] in merged_clique:
                merged_clique.add(other_clique[1])
            elif other_clique[1] in merged_clique:
                merged_clique.add(other_clique[0])
            else:
                cliques.append(other_clique)
        merged_cliques.append(merged_clique)

    return merged_cliques