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

from prolothar_process_discovery.models.bpmn.bpmn_process import BpmnProcess
from prolothar_process_discovery.models.bpmn.task import Task
from prolothar_process_discovery.models.bpmn.start_event import StartEvent
from prolothar_process_discovery.models.bpmn.end_event import EndEvent
from prolothar_process_discovery.models.bpmn.gateway import Gateway
from prolothar_process_discovery.models.bpmn.xor_gateway import XorGateway
from prolothar_process_discovery.models.bpmn.parallel_gateway import ParallelGateway
from prolothar_process_discovery.models.bpmn.sequence_flow import SequenceFlow

import tempfile
import os

class TestBpmnProcess(unittest.TestCase):

    def test_plot(self):
        bpmn_process = BpmnProcess()
        bpmn_process.add_start_event(StartEvent('start'))
        bpmn_process.add_end_event(EndEvent('end'))
        bpmn_process.add_task(Task.create_with_name_id('A'))
        bpmn_process.add_task(Task.create_with_name_id('B'))
        bpmn_process.add_task(Task.create_with_name_id('C'))
        bpmn_process.add_task(Task.create_with_name_id('D'))
        bpmn_process.add_task(Task.create_with_name_id('E'))
        bpmn_process.add_task(Task.create_with_name_id('F'))
        bpmn_process.add_task(Task.create_with_name_id('G'))
        bpmn_process.add_gateway(XorGateway('x_or_open',
                                 Gateway.Direction.DIVERGING))
        bpmn_process.add_gateway(XorGateway('x_or_close',
                                 Gateway.Direction.CONVERGING))
        bpmn_process.add_gateway(ParallelGateway('parallel_open',
                                 Gateway.Direction.DIVERGING))
        bpmn_process.add_gateway(ParallelGateway('parallel_close',
                                 Gateway.Direction.CONVERGING))
        bpmn_process.add_sequence_flow(SequenceFlow('0', 'start', 'A'))
        bpmn_process.add_sequence_flow(SequenceFlow('1', 'A', 'x_or_open'))
        bpmn_process.add_sequence_flow(SequenceFlow('2.1', 'x_or_open', 'B'))
        bpmn_process.add_sequence_flow(SequenceFlow('2.2', 'x_or_open', 'C'))
        bpmn_process.add_sequence_flow(SequenceFlow('3', 'B', 'x_or_close'))
        bpmn_process.add_sequence_flow(SequenceFlow('4', 'C', 'x_or_close'))
        bpmn_process.add_sequence_flow(SequenceFlow('5', 'x_or_close', 'parallel_open'))
        bpmn_process.add_sequence_flow(SequenceFlow('6', 'parallel_open', 'D'))
        bpmn_process.add_sequence_flow(SequenceFlow('7', 'parallel_open', 'E'))
        bpmn_process.add_sequence_flow(SequenceFlow('8', 'D', 'F'))
        bpmn_process.add_sequence_flow(SequenceFlow('9', 'E', 'G'))
        bpmn_process.add_sequence_flow(SequenceFlow('10', 'F', 'parallel_close'))
        bpmn_process.add_sequence_flow(SequenceFlow('11', 'G', 'parallel_close'))
        bpmn_process.add_sequence_flow(SequenceFlow('12', 'parallel_close', 'end'))

        plot = bpmn_process.plot(view=False)

        self.assertTrue(plot is not None)

    def test_split_mixed_gateways(self):
        bpmn_process = BpmnProcess()
        bpmn_process.add_start_event(StartEvent('start'))
        bpmn_process.add_task(Task.create_with_name_id('A'))
        bpmn_process.add_task(Task.create_with_name_id('B'))
        bpmn_process.add_task(Task.create_with_name_id('D'))
        bpmn_process.add_task(Task.create_with_name_id('E'))
        bpmn_process.add_gateway(XorGateway('x_or_open',
                                 Gateway.Direction.DIVERGING))
        bpmn_process.add_gateway(XorGateway('x_or_mixed',
                                 Gateway.Direction.MIXED))
        bpmn_process.add_sequence_flow(SequenceFlow('0', 'start', 'x_or_open'))
        bpmn_process.add_sequence_flow(SequenceFlow('1', 'x_or_open', 'A'))
        bpmn_process.add_sequence_flow(SequenceFlow('2', 'x_or_open', 'B'))
        bpmn_process.add_sequence_flow(SequenceFlow('3', 'A', 'x_or_mixed'))
        bpmn_process.add_sequence_flow(SequenceFlow('4', 'B', 'x_or_mixed'))
        bpmn_process.add_sequence_flow(SequenceFlow('5', 'x_or_mixed', 'x_or_open'))
        bpmn_process.add_sequence_flow(SequenceFlow('6', 'x_or_mixed', 'D'))
        bpmn_process.add_sequence_flow(SequenceFlow('7', 'x_or_mixed', 'E'))

        bpmn_process.split_mixed_gateways()

        expected_bpmn_process = BpmnProcess()
        expected_bpmn_process.add_start_event(StartEvent('start'))
        expected_bpmn_process.add_task(Task.create_with_name_id('A'))
        expected_bpmn_process.add_task(Task.create_with_name_id('B'))
        expected_bpmn_process.add_task(Task.create_with_name_id('D'))
        expected_bpmn_process.add_task(Task.create_with_name_id('E'))
        expected_bpmn_process.add_gateway(XorGateway('x_or_open',
                                 Gateway.Direction.DIVERGING))
        expected_bpmn_process.add_gateway(XorGateway('x_or_mixed_close',
                                 Gateway.Direction.CONVERGING))
        expected_bpmn_process.add_gateway(XorGateway('x_or_mixed_open',
                                 Gateway.Direction.DIVERGING))
        expected_bpmn_process.add_sequence_flow(SequenceFlow('0', 'start', 'x_or_open'))
        expected_bpmn_process.add_sequence_flow(SequenceFlow('1', 'x_or_open', 'A'))
        expected_bpmn_process.add_sequence_flow(SequenceFlow('2', 'x_or_open', 'B'))
        expected_bpmn_process.add_sequence_flow(SequenceFlow('3', 'A', 'x_or_mixed_close'))
        expected_bpmn_process.add_sequence_flow(SequenceFlow('4', 'B', 'x_or_mixed_close'))
        expected_bpmn_process.add_sequence_flow(SequenceFlow(
                'x_or_mixed_close_x_or_mixed_open', 'x_or_mixed_close', 'x_or_mixed_open'))
        expected_bpmn_process.add_sequence_flow(SequenceFlow('5', 'x_or_mixed_open', 'x_or_open'))
        expected_bpmn_process.add_sequence_flow(SequenceFlow('6', 'x_or_mixed_open', 'D'))
        expected_bpmn_process.add_sequence_flow(SequenceFlow('7', 'x_or_mixed_open', 'E'))

        self.assertEqual(
                expected_bpmn_process.plot(view=False),
                bpmn_process.plot(view=False))

    def test_save_to_xml_file(self):
        bpmn_process = BpmnProcess()
        bpmn_process.add_start_event(StartEvent('start'))
        bpmn_process.add_task(Task.create_with_name_id('A'))
        bpmn_process.add_task(Task.create_with_name_id('B'))
        bpmn_process.add_task(Task.create_with_name_id('D'))
        bpmn_process.add_task(Task.create_with_name_id('E'))
        bpmn_process.add_gateway(XorGateway('x_or_open',
                                 Gateway.Direction.DIVERGING))
        bpmn_process.add_gateway(XorGateway('x_or_mixed',
                                 Gateway.Direction.MIXED))
        bpmn_process.add_sequence_flow(SequenceFlow('0', 'start', 'x_or_open'))
        bpmn_process.add_sequence_flow(SequenceFlow('1', 'x_or_open', 'A'))
        bpmn_process.add_sequence_flow(SequenceFlow('2', 'x_or_open', 'B'))
        bpmn_process.add_sequence_flow(SequenceFlow('3', 'A', 'x_or_mixed'))
        bpmn_process.add_sequence_flow(SequenceFlow('4', 'B', 'x_or_mixed'))
        bpmn_process.add_sequence_flow(SequenceFlow('5', 'x_or_mixed', 'x_or_open'))
        bpmn_process.add_sequence_flow(SequenceFlow('6', 'x_or_mixed', 'D'))
        bpmn_process.add_sequence_flow(SequenceFlow('7', 'x_or_mixed', 'E'))

        with tempfile.TemporaryDirectory() as directory:
            xml_file = os.path.join(directory, 'bpmn.xml')
            self.assertFalse(os.path.exists(xml_file))
            bpmn_process.save_to_xml_file(xml_file)
            self.assertTrue(os.path.exists(xml_file))

if __name__ == '__main__':
    unittest.main()