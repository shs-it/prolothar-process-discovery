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

from prolothar_common.models.eventlog import EventLog, Trace
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.proseqo import Proseqo
from prolothar_process_discovery.discovery.proseqo.greedy_cover import compute_cover
from prolothar_process_discovery.discovery.proseqo.greedy_cover import GreedyCoverComputer
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.anomalydetection.traces.supervised_detector import SupervisedDetector

class ProseqoSupervised(SupervisedDetector):
    """
    uses the Proseqo algorithm for supervised anomaly detection.
    there will be a model for normal traces and a model for anomalies. depending
    on which model is able to give the shorter description, a trace will either
    be classified as normal or as anomaly.
    """

    def __init__(self, proseqo: Proseqo = Proseqo(), verbose: bool = False):
        self.__proseqo: Proseqo = proseqo
        self.__verbose: bool = verbose
        self.__normal_pattern_dfg: PatternDfg = None
        self.__anomalies_pattern_dfg: PatternDfg = None
        self.__normal_cover = None
        self.__anomalies_cover = None
        self.__normal_mdl: float = None
        self.__anomalies_mdl: float = None
        self.__normal_traces: EventLog = None
        self.__anomalies: EventLog = None

    def train(self, normal_traces: EventLog, anomalies: EventLog):
        self.__normal_pattern_dfg = PatternDfg.create_from_event_log(normal_traces)
        self.__anomalies_pattern_dfg = PatternDfg.create_from_event_log(anomalies)
        if self.__proseqo is not None:
            self.__normal_pattern_dfg = self.__proseqo.mine_dfg(
                normal_traces, self.__normal_pattern_dfg, verbose=self.__verbose)
            self.__anomalies_pattern_dfg = self.__proseqo.mine_dfg(
                anomalies, self.__anomalies_pattern_dfg, verbose=self.__verbose)
        self.__normal_cover = compute_cover(
            normal_traces.traces, self.__normal_pattern_dfg)
        self.__anomalies_cover = compute_cover(
            anomalies.traces, self.__anomalies_pattern_dfg)
        self.__normal_mdl = self.__normal_cover.get_encoded_length_of_cover(normal_traces)
        self.__anomalies_mdl = self.__anomalies_cover.get_encoded_length_of_cover(anomalies)
        self.__normal_traces = normal_traces
        self.__anomalies = anomalies

    def is_anomaly(self, trace: Trace) -> bool:
        normal_score = self.__compute_score(
            self.__normal_pattern_dfg, self.__normal_traces, self.__normal_cover,
            self.__normal_mdl, trace)
        anomaly_score = self.__compute_score(
            self.__anomalies_pattern_dfg, self.__anomalies,
            self.__anomalies_cover, self.__anomalies_mdl, trace)
        return anomaly_score < normal_score

    def __compute_score(
            self, model: PatternDfg, log_without_trace: EventLog,
            cover_without_trace, mdl_without_trace: float, trace: Trace) -> float:
        log = EventLog()
        log.traces = log_without_trace.traces + [trace]
        cover = cover_without_trace.copy_counts_only()
        cover.activity_set = cover.activity_set.union(trace.to_activity_list())

        mdl_with_trace = GreedyCoverComputer(model).compute(
            [trace], cover = cover).get_encoded_length_of_cover(log)

        return mdl_with_trace - mdl_without_trace



