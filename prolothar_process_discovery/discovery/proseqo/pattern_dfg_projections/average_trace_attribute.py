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
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_projections.abstract_numeric_projection import AbstractNumericProjection
from prolothar_common.experiments.statistics import Statistics

class AverageTraceAttribute(AbstractNumericProjection):
    """projects (colors nodes) in a PatternDfg based on the average value of
    a trace attribute
    """

    def __init__(self, log: EventLog, trace_attribute: str,
                 min_color = 'blue', max_color = 'red'):
        """
        Parameters
        ----------
        log : EventLog
            the log that is supposed to be projected onto the PatternDfg.
        trace_attribute : str
            the name of trace attribute whose average value is supposed to be
            projected onto the PatternDfg.
        Returns
        -------
        None.
        """
        super().__init__(min_color=min_color, max_color=max_color)
        self.__activity_statistics_dict = {
            activity: Statistics() for activity in log.compute_activity_set()
        }
        for trace in log.traces:
            attribute_value = trace.attributes.get(trace_attribute, None)
            if attribute_value is not None:
                for event in trace.events:
                    self.__activity_statistics_dict[event.activity_name].push(
                        attribute_value)
        self.__attribute = trace_attribute

    def get_attribute(self) -> str:
        return self.__attribute

    def _compute_node_value_dict(self, pattern_dfg: PatternDfg):
        node_value_dict = {}
        for node in pattern_dfg.get_nodes():
            node_statistics = Statistics()
            for activity in node.pattern.get_activity_set():
                node_statistics.merge(self.__activity_statistics_dict[activity])
            node_value_dict[node.activity] = node_statistics.mean()
        return node_value_dict

