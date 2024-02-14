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

from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg

class EdgeRemovalStrategy(ABC):
    @abstractmethod
    def remove_edges(
            self, dfg: PatternDfg, log: EventLog,
            verbose=False) -> PatternDfg:
        """
        folds a pattern-dfg by removing edges. the implementing subclass
        determines which edges should be removed

        Args:
            dfg:
                a pattern-directly-follows-graph
            log:
                can be used to determine whether an edge is important or not
            verbose:
                default is False. if true, debug messages are printed

        Returns:
            a PatternDfg with removed edges
        """
        pass