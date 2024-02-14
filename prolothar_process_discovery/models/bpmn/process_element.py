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

from abc import ABC, abstractmethod
from graphviz import Digraph

from lxml import etree

class ProcessElement(ABC):
    """an abstract definition of a process element in BPMN"""

    def __init__(self, element_id: str, name: str):
        """creates a new element. every alement has a unique id and a name
        that can be an empty string"""
        self.__id = element_id
        self.__name = name

    def get_name(self) -> str:
        return self.__name

    def get_id(self) -> str:
        return self.__id

    def __hash__(self) -> int:
        return hash(self.__id)

    def __eq__(self, other) -> int:
        return isinstance(other, ProcessElement) and other.__id == self.__id

    def is_gateway(self) -> bool:
        """returns True iff this element is some type of gateway"""
        return False

    @abstractmethod
    def add_to_graph(self, graph: Digraph):
        """adds the BPMN element to the graphviz graph.
        the concrete behavior is defined by the subclass
        """
        pass

    @abstractmethod
    def get_xml_tag_name(self) -> str:
        pass

    def create_xml_tag(self, parent_tag: etree.Element) -> etree.SubElement:
        element = etree.SubElement(parent_tag, self.get_xml_tag_name())
        element.set('id', self.get_id())
        element.set('name', self.get_name())
        return element