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

from typing import Tuple

from prolothar_common.models.eventlog import EventLog, Trace
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.proseqo import Proseqo
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.anomalydetection.oc3 import TrainedOc3
from prolothar_process_discovery.anomalydetection.pdfg_oc3 import PatternGraphOc3
from prolothar_process_discovery.anomalydetection.traces.supervised_detector import SupervisedDetector
from prolothar_process_discovery.anomalydetection.traces.unsupervised_detector import UnsupervisedDetector

class ProseqoOc3(SupervisedDetector, UnsupervisedDetector):
    """
    uses a combination of the Proseqo algorithm and the PatternGraphOc3 for
    anomaly detection. this can both be supervised or unsupervised.
    """

    def __init__(self, confidence_level: float = 0.2,
                 proseqo: Proseqo = Proseqo(), verbose: bool = False):
        self.__oc3: TrainedOc3 = None
        self.__confidence_level = confidence_level
        self.__proseqo = proseqo
        self.__verbose = verbose

    def train(self, normal_traces: EventLog, anomalies: EventLog):
        pattern_dfg = PatternDfg.create_from_event_log(normal_traces)
        if self.__proseqo is not None:
            pattern_dfg = self.__proseqo.mine_dfg(
                normal_traces, pattern_dfg, verbose=self.__verbose)
        self.__oc3 = PatternGraphOc3(
            pattern_dfg, normal_traces, devide_by_trace_length=True,
            compute_encoded_length_isolated=False).train_by_cantellis_inequality(
                self.__confidence_level)

    def is_anomaly(self, trace: Trace) -> bool:
        return self.__oc3.is_anomaly(trace)

    def compute_encoded_length(self, trace: Trace) -> float:
        """computes L(D|M)"""
        return self.__oc3.compute_encoded_length(trace)

    def apply(self, log: EventLog) -> Tuple[EventLog, EventLog]:
        self.train(log, None)
        normal_traces, anomalies = self.predict(log)
        self.__oc3 = None
        return normal_traces, anomalies
