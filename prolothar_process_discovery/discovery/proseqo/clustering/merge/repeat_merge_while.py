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

from typing import List, Callable

MergeCondition = Callable[[List[EventLog]], bool]

class RepeatMergeWhile(MergeStrategy):
    def __init__(self, merge_strategy: MergeStrategy,
                 merge_condition: MergeCondition):
        self.merge_strategy = merge_strategy
        self.merge_condition = merge_condition

    def merge(self, clusters: List[EventLog], verbose=False):
        self.merge_strategy.clear_cache()
        self.merge_condition.reset()
        while len(clusters) > 1 and self.merge_condition(clusters):
            self.merge_strategy.merge(clusters, verbose=verbose)
            if verbose:
                print('\rnr of clusters after merge iteration: %d ' % len(clusters), end = '\r')
        if verbose:
            #the progress print contains \r => print newline for next message
            print()

    def clear_cache(self):
        """deletes all cached information"""
        self.merge_strategy.clear_cache()

    def __repr__(self) -> str:
        return 'RepeatMergeWhile<%r, %r>' % (
                self.merge_strategy, self.merge_condition)

