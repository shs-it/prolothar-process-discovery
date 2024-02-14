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

from prolothar_process_discovery.discovery.proseqo.edge_removal.edge_removal_strategy import EdgeRemovalStrategy
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score

from prolothar_common.console_utils import print_progress_bar

from prolothar_common.parallel.abstract.computation_engine import ComputationEngine
from prolothar_common.parallel.single_thread.single_thread import SingleThreadComputationEngine

class MdlGreedy2(EdgeRemovalStrategy):
    """EdgeRemovalStrategy that sorts all edges ascending to their counts.
    Then for each edge it checked whether its removal decreases the mdl score
    and if so, it is removed"""

    def remove_edges(
            self, dfg: PatternDfg, log: EventLog,
            computation_engine: ComputationEngine = SingleThreadComputationEngine(),
            verbose=False):

        if dfg.get_nr_of_edges() > 0:
            current_mdl_score = compute_mdl_score(log, dfg)
            if verbose:
                print('MDL without any edges removed: %r' % current_mdl_score)

        filtered_dfg = dfg.copy()

        for i,edge in enumerate(sorted(dfg.edges.values(), key=lambda e: e.count)):
            candidate_dfg = filtered_dfg.copy()
            candidate_dfg.remove_edge((edge.start.activity, edge.end.activity))
            candidate_mdl_score = compute_mdl_score(log, candidate_dfg)
            if candidate_mdl_score < current_mdl_score:
                current_mdl_score = candidate_mdl_score
                filtered_dfg = candidate_dfg
            if verbose:
                print_progress_bar(i+1, dfg.get_nr_of_edges(),
                                   prefix='edge removal analysis:', length=50)

        return filtered_dfg.get_largest_weakly_connected_component()

    def __repr__(self) -> str:
        return 'MdlGreedy2'