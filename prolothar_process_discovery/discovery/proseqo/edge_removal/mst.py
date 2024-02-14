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

from collections import Counter
from math import ceil

from prolothar_common.parallel.abstract.computation_engine import ComputationEngine
from networkx import Graph, minimum_spanning_tree, connected_components

from prolothar_common.models.eventlog import EventLog, Trace
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.edge_removal.edge_removal_strategy import EdgeRemovalStrategy


class MinimumSpanningTree(EdgeRemovalStrategy):
    """implements denoising (until step 5 in algorithm 1) from
    "W. Li et al.: Anti-Noise Process Mining Algorithm Based on MST Clustering"
    """

    def __init__(self, noise_ratio: float):
        """creates a new instance

        Args:
            noise_ratio:
                the theta parameter. determines the amount of traces seen as
                noise in the log
        """
        if noise_ratio < 0 or noise_ratio > 1:
            raise ValueError('noise ration must be in interval [0,1]')
        self.__noise_ratio = noise_ratio

    def remove_edges(
            self, dfg: PatternDfg, log: EventLog,
            computation_engine: ComputationEngine = None,
            verbose=False):
        return PatternDfg.create_from_event_log(self.denoise_log(log))

    def denoise_log(self, log: EventLog) -> EventLog:
        """
        returns a sublog with all traces removed that are classified as noise.
        the remaining no-noise traces are returned unchanged, i.e. this method
        only filters traces and not activities.

        Parameters
        ----------
        log : EventLog
            will be cleaned

        Returns
        -------
        EventLog
            the cleaned log with noisy traces removed
        """
        mst = minimum_spanning_tree(self.__create_trace_distance_graph(log))

        sorted_edges = sorted(mst.edges(data=True), key=lambda e: -e[2]['weight'])

        for edge in sorted_edges[:ceil(self.__noise_ratio * log.get_nr_of_traces())]:
            mst.remove_edge(edge[0],edge[1])

        remaining_trace_numbers = set([
                node for node in
                max([mst.subgraph(c).copy() for c in connected_components(mst)],
                     key=len).nodes])

        denoised_log = EventLog()
        for i,trace in enumerate(log.traces):
            if i in remaining_trace_numbers:
                denoised_log.add_trace(trace)

        return denoised_log

    def __create_trace_distance_graph(self, log: EventLog):
        graph = Graph()

        graph.add_nodes_from(range(log.get_nr_of_traces()))

        for i,trace_i in enumerate(log.traces):
            for j,trace_j in enumerate(log.traces[i+1:], start=i+1):
                graph.add_edge(i,j,
                               weight=self.compute_trace_distance(trace_i,
                                                                  trace_j))

        return graph

    def compute_trace_distance(self, trace_k: Trace, trace_l: Trace) -> float:
        """
        computes a distance measure between trace_k and trace_l

        Parameters
        ----------
        trace_k : Trace
        trace_l : Trace

        Returns
        -------
        float
            the distance between trace_k and trace_l. the larger the higher
            the dissimilarity between trace_k and trace_l.
        """
        P_k = self.__compute_P(trace_k)
        P_l = self.__compute_P(trace_l)
        F_k = self.__compute_F(trace_k)
        F_l = self.__compute_F(trace_l)

        distance = 0
        all_activities = set(P_k.keys()).union(set(P_l.keys()))
        for activity_i in all_activities:
            for activity_j in all_activities:
                distance += abs(P_k[activity_i] * F_k[(activity_i,activity_j)] -
                                P_l[activity_i] * F_l[(activity_i,activity_j)])
        return 0.5 * distance

    def __compute_P(self, trace: Trace) -> Counter:
        counter = Counter()
        for event in trace.events:
            counter[event.activity_name] += 1
        return counter

    def __compute_F(self, trace: Trace) -> Counter:
        counter = Counter()
        for event_a, event_b in zip(trace.events, trace.events[1:]):
            counter[(event_a.activity_name, event_b.activity_name)] += 1
        return counter

    def __repr__(self) -> str:
        return 'MinimumSpanningTree'