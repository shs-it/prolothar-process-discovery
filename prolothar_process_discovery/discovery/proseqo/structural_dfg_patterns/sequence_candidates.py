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
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import find_isolated_sequences_in_dfg
from typing import Set

def find_sequence_candidates_in_dfg(dfg: DirectlyFollowsGraph) -> Set[Sequence]:
    """finds possible sequence pattern candidates by removing edges in the graph"""
    candidates = find_isolated_sequences_in_dfg(dfg)
    for edge in list(dfg.get_edges()):
        dfg.remove_edge((edge.start.activity, edge.end.activity))
        candidates.update(find_isolated_sequences_in_dfg(dfg))
        dfg.add_count(edge.start.activity, edge.end.activity, count=edge.count)
    for node in dfg.get_nodes():
        if len(node.edges) > 1:
            max_count = -1
            max_count_edge = None
            for edge in node.edges:
                if edge.count > max_count:
                    max_count = edge.count
                    max_count_edge = edge
            if not max_count_edge.is_self_loop():
                if hasattr(node, 'pattern') and node.pattern is not None:
                    candidates.add(Sequence([
                        node.pattern, max_count_edge.end.pattern
                    ]))
                else:
                    candidates.add(Sequence([
                        Singleton(node.activity),
                        Singleton(max_count_edge.end.activity)
                    ]))

    return candidates