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

from typing import Iterable, List

from graphviz import Digraph
from lxml import etree

import prolothar_common.gviz_utils as gviz_utils
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

from prolothar_process_discovery.models.bpmn.task import Task
from prolothar_process_discovery.models.bpmn.process_element import ProcessElement
from prolothar_process_discovery.models.bpmn.start_event import StartEvent
from prolothar_process_discovery.models.bpmn.end_event import EndEvent
from prolothar_process_discovery.models.bpmn.gateway import Gateway
from prolothar_process_discovery.models.bpmn.xor_gateway import XorGateway
from prolothar_process_discovery.models.bpmn.or_gateway import OrGateway
from prolothar_process_discovery.models.bpmn.parallel_gateway import ParallelGateway
from prolothar_process_discovery.models.bpmn.sequence_flow import SequenceFlow

class BpmnProcess():
    """a process in Business Process Modeling Notation"""

    def __init__(self):
        """creates a new, empty instance"""
        self.__dfg = DirectlyFollowsGraph()
        self.__all_elements_dict = {}
        self.__sequence_flows = {}

    def add_task(self, task: Task):
        """adds a new task to this process. raises an ValueError if there is
        already an element with the same id
        """
        self.__add_element(task, Task)

    def add_start_event(self, start_event: StartEvent):
        """adds a new start event to this process.
        raises an ValueError if there is already an element with the same id
        """
        self.__add_element(start_event, StartEvent)

    def add_end_event(self, end_event: EndEvent):
        """adds a new end event to this process.
        raises an ValueError if there is already an element with the same id
        """
        self.__add_element(end_event, EndEvent)

    def add_gateway(self, gateway: Gateway):
        """adds a gateway to this process. raises an ValueError if there is
        already an element with the same id"""
        self.__add_element(gateway, Gateway)

    def add_sequence_flow(self, sequence_flow: SequenceFlow):
        """adds a sequence flow to this process.

        Raises:
            ValueError:
                if there is already an element with the same id
            ValueError:
                if the referenced source or target does not exist
        """
        if sequence_flow.get_source_id() not in self.__all_elements_dict:
            raise ValueError('Referenced source with id %s does not exist' %
                             sequence_flow.get_source_id())
        if sequence_flow.get_target_id() not in self.__all_elements_dict:
            raise ValueError('Referenced target with id %s does not exist' %
                             sequence_flow.get_target_id())
        self.__add_element(sequence_flow, SequenceFlow)
        self.__dfg.add_count(sequence_flow.get_source_id(),
                             sequence_flow.get_target_id())
        self.__sequence_flows[(sequence_flow.get_source_id(),
                               sequence_flow.get_target_id())] = sequence_flow

    def remove_sequence_flow(self, sequence_flow: SequenceFlow):
        """removes the given sequence flow from this BPMN process"""
        edge_key = (sequence_flow.get_source_id(),
                    sequence_flow.get_target_id())
        self.__dfg.remove_edge(edge_key)
        self.__sequence_flows.pop(edge_key)
        self.__all_elements_dict.pop(sequence_flow.get_id())

    def get_dfg_with_element_ids(self) -> DirectlyFollowsGraph:
        return self.__dfg

    def get_all_elements(self) -> Iterable[ProcessElement]:
        return self.__all_elements_dict.values()

    def get_element_by_id(self, element_id: str) -> ProcessElement:
        return self.__all_elements_dict[element_id]

    def get_start_events(self) -> List[StartEvent]:
        return [event for event in self.get_all_elements()
                if isinstance(event, StartEvent)]

    def get_end_events(self) -> List[EndEvent]:
        return [event for event in self.get_all_elements()
                if isinstance(event, EndEvent)]

    def get_following_elements(self, element_id: str) -> Iterable[ProcessElement]:
        for following_element_id in self.__dfg.get_following_activities(element_id):
            yield self.get_element_by_id(following_element_id)

    def get_preceding_elements(self, element_id: str) -> Iterable[ProcessElement]:
        for preceding_element_id in self.__dfg.get_preceeding_activities(element_id):
            yield self.get_element_by_id(preceding_element_id)

    def __add_element(self, element: ProcessElement, element_type):
        if not isinstance(element, element_type):
            raise TypeError('element is not of type %r but of type %r' % (
                    element_type, type(element)))
        if element.get_id() in self.__all_elements_dict:
            raise ValueError('Element-ID %s already in use' % element.get_id())
        self.__all_elements_dict[element.get_id()] = element

    def plot(self, filepath: str = None, view: bool = True, filetype: str='pdf',
             layout: str='dot', concentrate_edges: bool = False) -> str:
        """returns the DOT source code of the plot"""
        graph = Digraph()
        if concentrate_edges:
            graph.attr('graph', concentrate='true')

        for element in sorted(self.get_all_elements(), key=ProcessElement.get_id):
            element.add_to_graph(graph)

        return gviz_utils.plot_graph(graph, view=view, filepath=filepath,
                                     filetype=filetype, layout=layout)

    def split_mixed_gateways(self):
        """replaces mixed gateways by an open gateway and a closed gateway
        """
        for element in list(self.get_all_elements()):
            if isinstance(element, Gateway) \
            and element.get_direction() == Gateway.Direction.MIXED:
                self.__split_mixed_gateway(element)

    def __split_mixed_gateway(self, mixed_gateway: Gateway):
        close_gateway = type(mixed_gateway)(
                mixed_gateway.get_id() + '_close',
                Gateway.Direction.CONVERGING)
        open_gateway = type(mixed_gateway)(
                mixed_gateway.get_id() + '_open',
                Gateway.Direction.DIVERGING)
        self.add_gateway(close_gateway)
        self.add_gateway(open_gateway)
        self.add_sequence_flow(SequenceFlow(
                close_gateway.get_id() + '_' + open_gateway.get_id(),
                close_gateway.get_id(),
                open_gateway.get_id()))
        for preceding_element in self.get_preceding_elements(
                mixed_gateway.get_id()):
            old_sequence_flow = self.__sequence_flows[
                    (preceding_element.get_id(), mixed_gateway.get_id())]
            self.remove_sequence_flow(old_sequence_flow)
            self.add_sequence_flow(SequenceFlow(old_sequence_flow.get_id(),
                                                preceding_element.get_id(),
                                                close_gateway.get_id()))
        for following_element in self.get_following_elements(
                mixed_gateway.get_id()):
            old_sequence_flow = self.__sequence_flows[
                    (mixed_gateway.get_id(), following_element.get_id())]
            self.remove_sequence_flow(old_sequence_flow)
            self.add_sequence_flow(SequenceFlow(old_sequence_flow.get_id(),
                                                open_gateway.get_id(),
                                                following_element.get_id()))
        self.__dfg.remove_node(mixed_gateway.get_id())
        self.__all_elements_dict.pop(mixed_gateway.get_id())

    @staticmethod
    def load_from_xml_file(filepath: str) -> 'BpmnProcess':
        """loads an instance from a xml file"""

        process = BpmnProcess()

        xml_tree = etree.parse(filepath)
        root = xml_tree.getroot()
        for process_element in root.findall("process/*", root.nsmap):
            if process_element.tag.endswith('task'):
                process.add_task(Task(process_element.attrib['id'],
                                      process_element.attrib['name']))
            elif process_element.tag.endswith('startEvent'):
                process.add_start_event(StartEvent(process_element.attrib['id']))
            elif process_element.tag.endswith('endEvent'):
                process.add_end_event(EndEvent(process_element.attrib['id']))
            elif process_element.tag.endswith('Gateway'):
                BpmnProcess.__add_gateway_to_process(process_element, process)
            elif process_element.tag.endswith('sequenceFlow'):
                process.add_sequence_flow(SequenceFlow(
                        process_element.attrib['id'],
                        process_element.attrib['sourceRef'],
                        process_element.attrib['targetRef']))
            else:
                print(process_element.tag)
                print(process_element.attrib)
                raise NotImplementedError(
                        'Unknown element type %s' % process_element.tag)

        return process

    def save_to_xml_file(self, filepath: str):
        """writes BPMN XML to the given filepath"""
        definitions = etree.Element('definitions')
        process = etree.SubElement(definitions, 'process')
        process.set('id', 'dummyprocessid')
        for element in self.get_all_elements():
            element.create_xml_tag(process)
        with open(filepath, 'wb') as f:
            f.write(etree.tostring(definitions))

    @staticmethod
    def __add_gateway_to_process(process_element, process: 'BpmnProcess'):
        if process_element.tag.endswith('exclusiveGateway'):
            gateway_type = XorGateway
        elif process_element.tag.endswith('parallelGateway'):
            gateway_type = ParallelGateway
        elif process_element.tag.endswith('inclusiveGateway'):
            gateway_type = OrGateway
        else:
            raise NotImplementedError('Gateway %s' % process_element.tag)

        gateway_direction_string = process_element.attrib['gatewayDirection']
        if gateway_direction_string == 'Converging':
            gateway_direction = Gateway.Direction.CONVERGING
        elif gateway_direction_string == 'Diverging':
            gateway_direction = Gateway.Direction.DIVERGING
        elif gateway_direction_string == 'Mixed':
            gateway_direction = Gateway.Direction.MIXED
        else:
            raise NotImplementedError(
                    'Gateway-Direction %s' % gateway_direction_string)

        process.add_gateway(
                gateway_type(process_element.attrib['id'], gateway_direction))
