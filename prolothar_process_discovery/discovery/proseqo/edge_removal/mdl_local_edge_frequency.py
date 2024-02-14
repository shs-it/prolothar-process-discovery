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

class MdlLocalEdgeFrequency(EdgeRemovalStrategy):

    def __init__(self, min_local_frequencies):
        if not min_local_frequencies:
            raise ValueError('min_local_frequencies must be a non-empty list or range')
        self.min_local_frequencies = min_local_frequencies
        self.min_local_frequencies.sort()

    def remove_edges(
            self, dfg: PatternDfg, log: EventLog,
            verbose=False) -> PatternDfg:

        if dfg.get_nr_of_edges() > 0:
            original_mdl_score = compute_mdl_score(log, dfg)

            best_mdl_score = original_mdl_score
            best_dfg = dfg

            for min_local_frequency in self.min_local_frequencies:
                try:
                    filtered_mdl_score, filtered_dfg = _compute_mdl_score_for_frequency(
                            dfg, log, min_local_frequency, verbose)
                except StopIteration:
                    break
                if filtered_mdl_score < best_mdl_score:
                    if verbose:
                        print(('edge frequency threshold %r improved mdl score '
                               'from %r to %r. %d nodes and %d edges left') % (
                                min_local_frequency, best_mdl_score,
                                filtered_mdl_score,
                                filtered_dfg.get_nr_of_nodes(),
                                filtered_dfg.get_nr_of_edges()))
                    best_mdl_score = filtered_mdl_score
                    best_dfg = filtered_dfg
                elif verbose:
                    print(('edge frequency threshold %r could not improve mdl score: '
                           '%r >= %r. %d nodes and %d edges would be left') % (
                               min_local_frequency, filtered_mdl_score,
                               best_mdl_score,
                               filtered_dfg.get_nr_of_nodes(),
                               filtered_dfg.get_nr_of_edges()))

        return best_dfg

    def __repr__(self) -> str:
        return 'MdlLocalEdgeFrequency<%r>' % self.min_local_frequencies

def _compute_mdl_score_for_frequency(dfg, log, min_local_frequency, verbose):
    filtered_dfg = PatternDfg.create_from_dfg(
        dfg.filter_edges_by_local_frequency(
            min_local_frequency).get_largest_weakly_connected_component())
    filtered_dfg.remove_not_allowed_start_activities(set(dfg.get_source_activities()))
    filtered_dfg.remove_not_allowed_end_activities(set(dfg.get_sink_activities()))
    if filtered_dfg.get_nr_of_nodes() == 0:
        if verbose:
            print('min_local_frequency %r leads to empty pattern dfg' % min_local_frequency)
        raise StopIteration()
    if not filtered_dfg.get_source_nodes() or not filtered_dfg.get_sink_nodes():
        if verbose:
            print('min_local_frequency %r removes source or sink nodes' % min_local_frequency)
        raise StopIteration()
    filtered_mdl_score = compute_mdl_score(log, filtered_dfg)

    return filtered_mdl_score, filtered_dfg
