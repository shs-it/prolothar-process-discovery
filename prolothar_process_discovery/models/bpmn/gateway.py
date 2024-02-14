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

from abc import abstractmethod
from typing import List

from prolothar_process_discovery.models.bpmn.process_element import ProcessElement

from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern

from enum import Enum, auto

from lxml import etree

class Gateway(ProcessElement):
    """a gateway element of a process in BPMN"""
    class Direction(Enum):
        CONVERGING = auto()
        DIVERGING = auto()
        MIXED = auto()

    def __init__(self, gateway_id: str, direction: Direction):
        super().__init__(gateway_id, '')
        self.__direction = direction

    def get_direction(self) -> 'Direction':
        return self.__direction

    def create_xml_tag(self, parent_tag: etree.Element) -> etree.SubElement:
        gateway = super().create_xml_tag(parent_tag)
        gateway.set('gatewayDirection', self.__direction_to_xml_string())
        return gateway

    def __direction_to_xml_string(self) -> str:
        if self.get_direction() == Gateway.Direction.CONVERGING:
            return 'Converging'
        elif self.get_direction() == Gateway.Direction.DIVERGING:
            return 'Diverging'
        elif self.get_direction() == Gateway.Direction.MIXED:
            return 'Mixed'
        else:
            raise NotImplementedError()

    def is_gateway(self) -> bool:
        return True

    @abstractmethod
    def create_pattern(self, branches: List[Pattern]) -> Pattern:
        pass
