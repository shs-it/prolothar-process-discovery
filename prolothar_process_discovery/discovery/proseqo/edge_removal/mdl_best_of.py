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

from prolothar_common.models.eventlog import EventLog

from prolothar_process_discovery.discovery.proseqo.edge_removal.edge_removal_strategy import EdgeRemovalStrategy
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score

class MdlBestOf(EdgeRemovalStrategy):

    def __init__(self, strategies: List[EdgeRemovalStrategy]):
        self.__strategies = strategies

    def remove_edges(
            self, dfg: PatternDfg, log: EventLog,
            verbose=False) -> PatternDfg:

        best_mdl = float('inf')
        best_dfg = dfg
        best_strategy = None

        for strategy in self.__strategies:
            strategy_dfg = strategy.remove_edges(dfg, log, verbose=verbose)
            strategy_mdl = compute_mdl_score(log, strategy_dfg)
            if verbose:
                print('tried %r with MDL %f' % (strategy, strategy_mdl))
            if strategy_mdl < best_mdl:
                best_mdl = strategy_mdl
                best_dfg = strategy_dfg
                best_strategy = strategy
        if verbose:
            print('selected %r as best with MDL %r' % (best_strategy, best_mdl))

        return best_dfg

    def __repr__(self) -> str:
        return 'MdlBestOf<%r>' % self.__strategies

