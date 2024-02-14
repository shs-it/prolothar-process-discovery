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

from prolothar_process_discovery.discovery.proseqo.edge_removal.edge_removal_strategy import EdgeRemovalStrategy

class EdgeRemoval(DfgAbstractionStrategy):
    """implementation of DfgAbstractionStrategy that is an adapter to the
    edge removal strategies. this is especially useful with the Union strategy.
    """

    def __init__(self, edge_removal_strategy: EdgeRemovalStrategy):
        """creates a new instance of this dfg abstraction strategy

        Args:
            edge_removal_strategy:
                the underlying EdgeRemovalStrategy that will be applied on the
                pattern_dfg
        """
        self.__edge_removal_strategy = edge_removal_strategy

    def mine_dfg(self, log: EventLog, dfg: DirectlyFollowsGraph,
                 verbose: bool = False):
        return self.__edge_removal_strategy.remove_edges(
            dfg, log, verbose=verbose)

    def __repr__(self) -> str:
        return ('EdgeRemoval(%r)' % self.__edge_removal_strategy)
