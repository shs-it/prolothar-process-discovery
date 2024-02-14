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
from prolothar_process_discovery.discovery.proseqo.clustering.merge.merge_strategy import MergeStrategy
from prolothar_common.models.eventlog import EventLog

from typing import List

class AndMerge(MergeStrategy):
    def __init__(self, first_strategy: MergeStrategy,
                 second_strategy: MergeStrategy):
        self.first_strategy = first_strategy
        self.second_strategy = second_strategy

    def merge(self, clusters: List[EventLog], verbose=False):
        if verbose:
            print('start merging with first strategy %r' % self.first_strategy)
        self.first_strategy.merge(clusters, verbose=verbose)
        if verbose:
            print('start merging with second strategy %r' % self.second_strategy)
        self.second_strategy.merge(clusters, verbose=verbose)

    def clear_cache(self):
        """deletes all cached information"""
        self.first_strategy.clear_cache()
        self.second_strategy.clear_cache()

    def __repr__(self) -> str:
        return 'AndMerge<%r, %r>' % (self.first_strategy, self.second_strategy)