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

from prolothar_process_discovery.models.bpmn.process_element import ProcessElement

from graphviz import Digraph

from lxml import etree

class SequenceFlow(ProcessElement):
    """a sequence flow element of a process in BPMN that combines other elements"""
    def __init__(self, element_id: str, source_id: str, target_id: str):
        super().__init__(element_id, '')
        self.__source_id = source_id
        self.__target_id = target_id

    def get_source_id(self) -> str:
        return self.__source_id

    def get_target_id(self) -> str:
        return self.__target_id

    def add_to_graph(self, graph: Digraph):
        graph.edge(self.__source_id,
                   self.__target_id)

    def create_xml_tag(self, parent_tag: etree.Element) -> etree.SubElement:
        sequence_flow = super().create_xml_tag(parent_tag)
        sequence_flow.set('sourceRef', self.get_source_id())
        sequence_flow.set('targetRef', self.get_target_id())
        return sequence_flow

    def get_xml_tag_name(self) -> str:
        return 'sequenceFlow'