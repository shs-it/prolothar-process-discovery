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

from typing import Dict, Tuple, Set
from math import exp

from prolothar_common.parallel.abstract.computation_engine import ComputationEngine
from prolothar_common.parallel.single_thread.single_thread import SingleThreadComputationEngine

class Probabilistic(EdgeRemovalStrategy):
    """EdgeRemovalStrategy that implements the ideas from
    "A Probabilistic Approach for Process Mining in Incomplete and Noise Logs"
    by Farkhady and Aali
    """

    def remove_edges(
            self, dfg: PatternDfg, log: EventLog,
            computation_engine: ComputationEngine = SingleThreadComputationEngine(),
            verbose=False):

        count_a_dotdot_b = log.count_follows_directly_or_indirectly()
        nr_of_distinct_activities = len(log.compute_activity_set())

        filtered_dfg = dfg.copy()

        for edge in list(filtered_dfg.get_edges()):
            if not self.__direct_successors(
                    edge.start.activity, edge.end.activity, count_a_dotdot_b,
                    log, nr_of_distinct_activities, dfg):
                filtered_dfg.remove_edge((edge.start.activity,
                                          edge.end.activity))

        return filtered_dfg

    def __direct_successors(
            self, a: str, b: str, count_a_dotdot_b: Dict[Tuple[str,str],int],
            log: EventLog, nr_of_distinct_activities: int,
            dfg: PatternDfg) -> bool:
        return (self.__probability_parallel(
                a, b, count_a_dotdot_b, log, nr_of_distinct_activities) < 0.2 and
                self.__mean_distance(a,b,count_a_dotdot_b,log,
                                     nr_of_distinct_activities, dfg) < 2.5 and
                self.__compute_F_A_follows_B(a,b,dfg) > 0.9)

    def __probability_parallel(self, a: str, b: str,
                               count_a_dotdot_b: Dict[Tuple[str,str],int],
                               log: EventLog, nr_of_distinct_activities: int,
                               K=20) -> float:
       N = count_a_dotdot_b[(a,b)] + count_a_dotdot_b[(b,a)]
       x = count_a_dotdot_b[(a,b)] / N
       theta = self.__compute_theta(a, b, log, nr_of_distinct_activities)
       return (N / (N + 1)) * exp(-((1.25 / (0.5 - theta))*(x - 0.5)) ** K)

    def __compute_theta(self, a, b, log, nr_of_distinct_activities, F=0.01):
       L = 0
       for trace in log.traces:
          if trace.contains_activity(a) and trace.contains_activity(b):
              L += 1
       return 1 + round((F * L) / (3 * nr_of_distinct_activities))

    def __mean_distance(self, a: str, b: str,
                        count_a_dotdot_b: Dict[Tuple[str,str],int],
                        log: EventLog,nr_of_distinct_activities:int,
                        dfg: PatternDfg) -> float:
        delta = 1
        for inbetween_activity in self.__get_activities_between(a,b,log):
            if self.__ds(a,inbetween_activity,dfg,log,nr_of_distinct_activities):
                delta += (1 - self.__probability_parallel(
                        inbetween_activity,b,count_a_dotdot_b,log,
                        nr_of_distinct_activities))
            elif (self.__ds(inbetween_activity,b,dfg,log,nr_of_distinct_activities)
                  and self.__ds(a,b,dfg,log,nr_of_distinct_activities)):
                delta += (1 - self.__probability_parallel(
                        a,inbetween_activity,count_a_dotdot_b,
                        log,nr_of_distinct_activities))
            else:
                delta += (1 - self.__probability_parallel(
                        a,inbetween_activity,count_a_dotdot_b,log,
                        nr_of_distinct_activities) * self.__probability_parallel(
                                inbetween_activity,b,count_a_dotdot_b,log,
                                nr_of_distinct_activities))
        if delta > 3:
            delta = 3
        return delta

    def __get_activities_between(self, a: str, b: str, log: EventLog) -> Set[str]:
        between_activities = set()
        for trace in log.traces:
            a_seen = False
            candidates = set()
            for event in trace.events:
                if event.activity_name == a:
                    a_seen = True
                elif event.activity_name == b:
                    if a_seen:
                        between_activities = between_activities.union(candidates)
                        candidates = set()
                        a_seen = False
                elif a_seen:
                    candidates.add(event.activity_name)
        return between_activities

    def __ds(self, a: str, b: str, dfg: PatternDfg, log: EventLog,
             nr_of_distinct_activities: int) -> bool:
        N = dfg.get_count(a,b) + dfg.get_count(b,a)
        F_A_follows_B = (dfg.get_count(a,b) - dfg.get_count(b,a)) / (N + 1)
        F_B_follows_A = (dfg.get_count(b,a) - dfg.get_count(a,b)) / (N + 1)
        F_A_parallel_B = (1 - F_A_follows_B) * N / (N + 1)
        F_A_hash_B = 1 - N / (N + 1)
        return (
            F_A_follows_B > F_B_follows_A and
            F_A_follows_B > F_A_parallel_B and
            F_A_follows_B > F_A_hash_B
        )

    def __compute_F_A_follows_B(self, a, b, dfg) -> float:
        N = dfg.get_count(a,b) + dfg.get_count(b,a)
        return (dfg.get_count(a,b) - dfg.get_count(b,a)) / (N + 1)

    def __repr__(self) -> str:
        return 'Probabilistic'