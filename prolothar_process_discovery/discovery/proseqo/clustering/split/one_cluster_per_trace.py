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
from prolothar_process_discovery.discovery.proseqo.clustering.split.split_strategy import SplitStrategy
from prolothar_common.models.eventlog import EventLog

from typing import List

class OneClusterPerTrace(SplitStrategy):
    def split(self, log: EventLog, verbose=False) -> List[EventLog]:
        clusters = []
        for trace in log.traces:
            cluster = EventLog()
            cluster.add_trace(trace)
            clusters.append(cluster)
        return clusters

    def __repr__(self) -> str:
        return 'OneClusterPerTrace'