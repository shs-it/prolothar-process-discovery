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
from typing import Dict

from matplotlib.colors import Colormap, LinearSegmentedColormap
from prolothar_common.color_utils import is_light_or_dark_rgb

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg

class AbstractNumericProjection(ABC):
    """projects (colors nodes) in a PatternDfg based on the numeric aggregation
    of one or multiple trace attributes.
    """

    def __init__(self, min_color = 'blue', max_color = 'red'):
        """
        Parameters
        ----------
        log : EventLog
            the log that is supposed to be projected onto the PatternDfg.
        """
        self.__color_map = LinearSegmentedColormap.from_list(
            'blue2red', [min_color, 'white', max_color])

    def get_color_map(self) -> Colormap:
        return self.__color_map

    def get_min_value(self) -> float:
        return self.__min_value

    def get_max_value(self) -> float:
        return self.__max_value

    def get_attribute(self) -> str:
        return self.__attribute

    def project(self, pattern_dfg: PatternDfg):
        """
        sets color and font color of the nodes

        Parameters
        ----------
        pattern_dfg : PatternDfg
            the PatternDfg on which we want to project log attributes

        Returns
        -------
        None.

        """
        node_value_dict = self._compute_node_value_dict(pattern_dfg)
        non_none_values = [value for value in node_value_dict.values()
                           if value is not None]
        self.__min_value = min(non_none_values)
        self.__max_value = max(non_none_values)
        for node_id, value in node_value_dict.items():
            if self.__min_value == self.__max_value or value is None:
                color_tuple = self.__color_map(0.5)
            else:
                color_tuple = self.__color_map(
                    (value - self.__min_value) /
                    (self.__max_value - self.__min_value))
            color_tuple = tuple(int(c * 255) for c in color_tuple)
            pattern_dfg.nodes[node_id].color = '#%02x%02x%02x%02x' % color_tuple
            if is_light_or_dark_rgb(color_tuple[:3]) == 'light':
                pattern_dfg.nodes[node_id].fontcolor = 'black'
            else:
                pattern_dfg.nodes[node_id].fontcolor = 'white'

    @abstractmethod
    def _compute_node_value_dict(
            self, pattern_dfg: PatternDfg) -> Dict[str,float]:
        """computes the aggregated value per node. the node with the minimal
        value will be colored with the defined minimum color and the node with
        the maximum value will be colored with the defined maximum color. all
        other nodes will be colored with a gradient.
        """
        pass
