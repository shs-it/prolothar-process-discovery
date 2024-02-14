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

from prolothar_process_discovery.discovery.proseqo.edge_removal.edge_removal_strategy import EdgeRemovalStrategy
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.anti_swap_noise_edge_removal_generator import AntiSwapNoiseEdgeRemovalCandidateGenerator

class AntiSwap(EdgeRemovalStrategy):

    def __init__(self, threshold: float):
        self.__threshold = threshold

    def remove_edges(
            self, dfg: PatternDfg, log: EventLog,
            verbose=False) -> PatternDfg:

        dfg = dfg.copy()
        for edge_removal in AntiSwapNoiseEdgeRemovalCandidateGenerator(
                self.__threshold).generate_candidates(log, None, dfg):
            edge_removal.apply_on_dfg(dfg)

        return dfg

    def __repr__(self) -> str:
        return 'AntiSwap<%r>' % self.__threshold

