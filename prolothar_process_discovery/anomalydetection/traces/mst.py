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

from prolothar_process_discovery.discovery.proseqo.edge_removal.mst import MinimumSpanningTree as MST
from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.anomalydetection.traces.unsupervised_detector import UnsupervisedDetector

class MinimumSpanningTree(UnsupervisedDetector):
    """
    uses  denoising (until step 5 in algorithm 1) from
    "W. Li et al.: Anti-Noise Process Mining Algorithm Based on MST Clustering"
    """

    def __init__(self, noise_ratio: float = 0.02):
        self.__noise_ratio = noise_ratio

    def apply(self, log: EventLog) -> Tuple[EventLog, EventLog]:
        normal_traces = MST(self.__noise_ratio).denoise_log(log)
        normal_trace_ids = set(trace.get_id() for trace in normal_traces)
        anomalies = EventLog()
        for trace in log:
            if trace.get_id() not in normal_trace_ids:
                anomalies.add_trace(trace)
        return normal_traces, anomalies