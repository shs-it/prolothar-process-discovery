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
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.covering_pattern.covering_pattern import CoveringPattern

from typing import Set

class CoveringClustering(CoveringPattern):

    def __init__(self, clustering: Pattern, trace, last_covered_activity: str):
        super().__init__(clustering, trace, last_covered_activity)
        self.covering_subpattern = None

    def process_covering_step(self, cover, last_activity: str,
                              next_activity: str):
        if self.completed_covering:
            raise ValueError('covering already completed')
        if not self.started_covering:
            self.started_covering = True
            cluster_index = self.pattern.trace_to_community_index_dict[self.trace]
            self.covering_subpattern = self.pattern.get_subpatterns()[
                    cluster_index].for_covering(self.trace, last_activity)
            if not self.covering_subpattern.pattern.contains_activity(next_activity):
                cover.add_log_move(last_activity, next_activity, set())
                return
        self.covering_subpattern.process_covering_step(
                cover, last_activity, next_activity)
        self.completed_covering = self.covering_subpattern.completed_covering

    def skip_to_end(self, cover, trace, last_covered_activity: str):
        self.completed_covering = True
        if self.covering_subpattern is not None:
            return self.covering_subpattern.skip_to_end(
                    cover, trace, last_covered_activity)
        else:
            return self.pattern.get_cluster_for_trace(trace).for_covering(
                    trace, last_covered_activity).skip_to_end(
                            cover, trace, last_covered_activity)

    def _get_next_coverable_activities(self) -> Set[str]:
        return self.covering_subpattern.get_next_coverable_activities()

    def can_cover(self, activity: str) -> bool:
        if self.covering_subpattern is not None:
            return self.covering_subpattern.can_cover(activity)
        else:
            cluster_index = self.pattern.trace_to_community_index_dict[self.trace]
            return self.pattern.get_subpatterns()[cluster_index].contains_activity(activity)
