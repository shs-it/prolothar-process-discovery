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

from typing import List, Set

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.cover import Cover
from prolothar_common.models.eventlog import Trace

def compute_cover(trace_list: List[Trace], pattern_dfg: PatternDfg,
                  store_patterns_in_pattern_stream: bool = False,
                  activity_set: Set[str]=None) -> Cover:
    """computes a Cover for a PatternDfg on a given list of Traces. This
    method is a convenience method that uses an instance of
    GreedyCoverComputer"""
    ...

class GreedyCoverComputer():
    """computes a Cover for a PatternDfg on a given list of Traces"""
    def __init__(self, pattern_dfg: PatternDfg): ...

    def compute(self, trace_list: List[Trace],
                store_patterns_in_pattern_stream: bool = False,
                activity_set: Set[str] = None,
                cover: Cover = None) -> Cover:
        """computes a Cover for a PatternDfg on a given list of Traces"""
        ...
