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

import unittest

import pandas as pd

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_projections.average_trace_attribute import AverageTraceAttribute
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_projections.average_trace_attribute_on_node_level import AverageTraceAttributeOnNodeLevel
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_projections.sum_of_trace_attribute_on_node_level import SumOfTraceAttributeOnNodeLevel
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_projections.sum_divided_by_sum_trace_attribute_on_node_level import SumDividedBySumTraceAttributeOnNodeLevel

class TestProjectLogAttribute(unittest.TestCase):

    def setUp(self):
        csv_log = pd.read_csv(
                'prolothar_tests/resources/logs/example_log_for_statistics.csv',
                delimiter=',')

        self.log = EventLog.create_from_pandas_df(
                csv_log, 'TraceId', 'Activity',
                event_attribute_columns=['Duration'],
                trace_attribute_columns=['Temperature', 'Age', 'Constant'])

        self.dfg = PatternDfg.create_from_event_log(self.log)

    def test_project_avg_trace_attribute(self):
        AverageTraceAttribute(self.log, 'Temperature').project(self.dfg)
        self.assertTrue(self.dfg.plot(view=False) is not None)

    def test_project_avg_trace_attribute_on_constant(self):
        AverageTraceAttribute(self.log, 'Constant').project(self.dfg)
        self.assertTrue(self.dfg.plot(view=False) is not None)

    def test_project_avg_trace_attribute_on_node_level(self):
        AverageTraceAttributeOnNodeLevel(self.log, 'Temperature').project(self.dfg)
        self.assertTrue(self.dfg.plot(view=False) is not None)

    def test_project_sum_of_trace_attribute_on_node_level(self):
        SumOfTraceAttributeOnNodeLevel(self.log, 'Temperature').project(self.dfg)
        self.assertTrue(self.dfg.plot(view=False) is not None)

    def test_project_sum_divided_by_sum_trace_attribute_on_node_level(self):
        SumDividedBySumTraceAttributeOnNodeLevel(
            self.log, 'Temperature', 'Age').project(self.dfg)
        self.assertTrue(self.dfg.plot(view=False) is not None)

if __name__ == '__main__':
    unittest.main()