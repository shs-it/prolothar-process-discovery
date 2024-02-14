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

from typing import List

from graphviz import Digraph

from prolothar_process_discovery.models.bpmn.gateway import Gateway
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.pattern.inclusive_choice import InclusiveChoice

class OrGateway(Gateway):
    """an inclusive or gateway in a process"""

    def __init__(self, gateway_id: str, direction: Gateway.Direction):
        super().__init__(gateway_id, direction)

    def create_pattern(self, branches: List[Pattern]) -> InclusiveChoice:
        return InclusiveChoice(branches)

    def add_to_graph(self, graph: Digraph):
        graph.node(self.get_id(), shape="diamond", label="O")

    def get_xml_tag_name(self) -> str:
        return 'inclusiveGateway'