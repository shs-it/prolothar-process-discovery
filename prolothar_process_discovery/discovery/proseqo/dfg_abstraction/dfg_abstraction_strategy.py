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
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

from abc import ABC, abstractmethod

class DfgAbstractionStrategy(ABC):
    """interface for an algorithm that creates a pattern-dfg given a dfg and an
    event log
    """

    @abstractmethod
    def mine_dfg(self, log: EventLog, dfg: DirectlyFollowsGraph,
                 verbose: bool = False):
        """creates a pattern-dfg given a dfg and an event log
        """
        pass
