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
from typing import List
from prolothar_process_discovery.anomalydetection.oc3 import Oc3

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.greedy_cover import compute_cover
from prolothar_process_discovery.discovery.proseqo.greedy_cover import GreedyCoverComputer

class PatternGraphOc3(Oc3):
    """
    Oc3 anomaly detection implementation for PatternDfg
    """

    def __init__(self, pattern_graph: PatternDfg, log: EventLog,
                 devide_by_trace_length: bool = False,
                 compute_encoded_length_isolated: bool = True):
        self.__pattern_graph = pattern_graph
        self.__activity_set = log.compute_activity_set()
        self.__cover = compute_cover(log.traces, self.__pattern_graph,
                                     activity_set = self.__activity_set)
        super().__init__(
            log, devide_by_instance_length=devide_by_trace_length,
            compute_encoded_length_isolated=compute_encoded_length_isolated)

    def _compute_encoded_length_of_instance(self, instance) -> float:
        return self.compute_encoded_length_of_dataset([instance])

    def compute_encoded_length_of_dataset(self, dataset) -> float:
        log = EventLog()
        log.traces = dataset
        cover = compute_cover(log.traces, self.__pattern_graph,
                              activity_set = self.__activity_set)
        return cover.get_encoded_length_of_cover(log)

    def _compute_encoded_length_of_additional_instance(
            self, dataset_without_instance: List, instance) -> float:
        cover = self.__cover.copy_counts_only()
        log = EventLog()
        log.traces = dataset_without_instance + [instance]
        cover.activity_set = cover.activity_set.union(instance.to_activity_list())
        return GreedyCoverComputer(self.__pattern_graph).compute(
            [instance], cover = cover).get_encoded_length_of_cover(log)

    def get_cover(self):
        return self.__cover
