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
from prolothar_process_discovery.discovery.proseqo.edge_removal.event_recall.event_recall import EventRecall
from prolothar_process_discovery.discovery.proseqo.edge_removal.event_recall.event_connectivity_recall import EventConnectivityRecall

from prolothar_process_discovery.discovery.proseqo.edge_removal.edge_removal_strategy import EdgeRemovalStrategy
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg

class EventRecallEdgePruning(EdgeRemovalStrategy):
    """EdgeRemovalStrategy that removes edge in increasing order of their count.
    An edge is removed if its removal does not decrease event recall below a
    given threshold.
    """

    def __init__(self, min_recall: float, recall:
                 EventRecall = EventConnectivityRecall(),
                 stop_on_first_violating_edge: bool = False,
                 max_edge_removals_per_call: int = None):
        self.__min_recall = min_recall
        self.__recall = recall
        self.__stop_on_first_violating_edge = stop_on_first_violating_edge
        self.__max_edge_removals_per_call = max_edge_removals_per_call

    def remove_edges(
            self, dfg: PatternDfg, log: EventLog, verbose=False) -> PatternDfg:
        if verbose:
            print('start edge pruning by recall (min_recall = %r)' % self.__min_recall)

        log = log.copy()

        dfg = dfg.copy()

        nr_of_removed_edges = 0

        for edge in sorted(dfg.get_edges(), key = lambda edge: edge.count):
            if self.__max_edge_removals_per_call is not None \
            and nr_of_removed_edges >= self.__max_edge_removals_per_call:
                print('limit of %d removed edges for this call reached' %
                      self.__max_edge_removals_per_call)
                break
            dfg.remove_edge((edge.start.activity, edge.end.activity))
            new_recall = self.__recall.compute(dfg.expand(), log)
            if new_recall < self.__min_recall:
                if verbose:
                    print('removal of "%s->%s" would make recall fall below threshold. %r < %r' % (
                            edge.start.activity, edge.end.activity, new_recall, self.__min_recall))
                dfg.add_count(edge.start.activity, edge.end.activity,
                              count = edge.count)
                if self.__stop_on_first_violating_edge:
                    break
            elif verbose:
                nr_of_removed_edges += 1
                print('removed "%s->%s". current recall: %r' % (
                        edge.start.activity, edge.end.activity, new_recall))
        return dfg

    def __repr__(self) -> str:
        return 'EventRecallEdgePruning(%r)' % self.__min_recall

