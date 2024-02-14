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
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_projections.sum_of_trace_attribute_on_node_level import SumOfTraceAttributeOnNodeLevel

class SumDividedBySumTraceAttributeOnNodeLevel(AbstractNumericProjection):
    """projects (colors nodes) in a PatternDfg based on the summed value of
    a trace attribute. per high-level node, a plate's value is counted at most once.
    """

    def __init__(self, log: EventLog, trace_attribute_nominator: str,
                 trace_attribute_denominator: str,
                 min_color = 'blue', max_color = 'red'):
        """
        Parameters
        ----------
        log : EventLog
            the log that is supposed to be projected onto the PatternDfg.
        trace_attribute_nominator : str
            the name of trace attribute whose sum value is divided by the
            sum of trace_attribute_denominator
        trace_attribute_denominator : str
            name of trace attribute whose sum value is in the denominator
            for computing the aggregated node value for projection
        Returns
        -------
        None.
        """
        super().__init__(min_color=min_color, max_color=max_color)
        self.__log = log
        self.__trace_attribute_nominator = trace_attribute_nominator
        self.__trace_attribute_denominator = trace_attribute_denominator

    def _compute_node_value_dict(self, pattern_dfg: PatternDfg):
        node_value_dict_nominator = SumOfTraceAttributeOnNodeLevel(
            self.__log, self.__trace_attribute_nominator
        )._compute_node_value_dict(pattern_dfg)
        node_value_dict_denominator = SumOfTraceAttributeOnNodeLevel(
            self.__log, self.__trace_attribute_denominator
        )._compute_node_value_dict(pattern_dfg)

        node_value_dict = {}
        for node, value in node_value_dict_nominator.items():
            if node_value_dict_denominator[node] == 0:
                node_value_dict[node] = None
            else:
                node_value_dict[node] = value / node_value_dict_denominator[node]
        return node_value_dict
