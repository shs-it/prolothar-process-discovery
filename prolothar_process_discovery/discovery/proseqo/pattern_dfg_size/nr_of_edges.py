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

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_size.pattern_dfg_size import PatternDfgSize

class NrOfEdges(PatternDfgSize):
    """computes the size of a PatternDfg as the number of high-level edges"""

    def compute_size(self, dfg: PatternDfg) -> float:
        """returns the number of high-level edges in the PatternDfg"""
        return dfg.get_nr_of_edges()

    def __repr__(self) -> str:
        return 'NrOfEdges'