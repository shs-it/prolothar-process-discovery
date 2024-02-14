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

from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.dfg_abstraction_strategy import DfgAbstractionStrategy

from prolothar_common.models.eventlog import EventLog
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

from typing import List

class Union(DfgAbstractionStrategy):
    """applies all sub-strategies in sequence
    """

    def __init__(self, substrategies: List[DfgAbstractionStrategy]):
        self.__substrategies = substrategies

    def mine_dfg(self, log: EventLog, dfg: DirectlyFollowsGraph,
                 verbose: bool = False):
        pattern_dfg = dfg
        for substrategy in self.__substrategies:
            pattern_dfg = substrategy.mine_dfg(
                log, pattern_dfg, verbose = verbose)
        return pattern_dfg

    def __repr__(self) -> str:
        return 'Union(%r)' % self.__substrategies