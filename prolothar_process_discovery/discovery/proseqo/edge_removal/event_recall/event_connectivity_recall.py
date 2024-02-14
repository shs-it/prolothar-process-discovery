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

from prolothar_process_discovery.discovery.proseqo.edge_removal.event_recall.event_recall import EventRecall

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.eventlog import EventLog, Trace

class EventConnectivityRecall(EventRecall):
    """implementation of EventRecall that rewards connectivity between following
    activities in a trace
    """

    def compute(self, dfg: DirectlyFollowsGraph, log: EventLog) -> float:
        for trace in log.traces:
            self.__mark_recalled_events_in_trace(trace, dfg)

        recalled_events = 0
        total_events = 0
        for trace in log.traces:
            for event in trace.events:
                total_events += 1
                if event.attributes['recalled']:
                    recalled_events += 1
        return recalled_events / total_events

    def __mark_recalled_events_in_trace(
            self, trace: Trace, dfg: DirectlyFollowsGraph):

        for event in trace.events[1:]:
            event.attributes['recalled'] = False

        trace.events[0].attributes['recalled'] = trace.events[0].activity_name in dfg.nodes

        i = 0
        while i < len(trace):
            for j in range(i+1, len(trace)):
                if (trace.events[i].activity_name,
                    trace.events[j].activity_name) in dfg.edges \
                or dfg.compute_shortest_path(trace.events[i].activity_name,
                                             trace.events[j].activity_name):
                    trace.events[j].attributes['recalled'] = True
                    i = j
                    break
            else:
                break
