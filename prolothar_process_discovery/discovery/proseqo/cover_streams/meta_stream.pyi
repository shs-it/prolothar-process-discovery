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
from typing import List, Union, Tuple, Dict, Set

Metacode = Union[Pattern,str]
class MetaStream:
    def __init__(self): ...

    def copy_counts_only(self) -> 'MetaStream':
        """returns a copy of this stream. Only the counts are copied.
        All caches and any other information is not copied
        """
        ...

    def add_present_code(self, pattern: Pattern, last_covered_activity: str):
        """adds a "present" meta code"""
        ...

    def add_absent_code(self, pattern: Pattern, last_covered_activity: str):
        """adds a "absent" meta code"""
        ...

    def add_repeat_code(self, pattern: Pattern, iteration: int,
                        last_covered_activity: str):
        """adds a "repeat" meta code"""
        ...

    def add_end_code(self, pattern: Pattern, iteration: int,
                     last_covered_activity: str):
        """adds an "end" meta code"""
        ...

    def add_routing_code(self, pattern: Pattern, subpattern: Pattern,
                         subpattern_alternatives: List[Metacode],
                         last_covered_activity: str):
        """adds a "routing"-code to the metastream

        Args:
            pattern:
                the pattern for which the routing code is supposed to be
                added to the stream
            subpattern:
                the routing code, i.e. the subpattern that is used in the cover
            subpattern_alternatives:
                the alternatives that were available. this is used
                to compute the encoding length of the routing code. this should
                be inclusive the subpattern
        """
        ...

    def get_code_length(self, verbose=False) -> float:
        """returns the code length of this meta stream using optimal prefix codes"
        """
        ...

    def get_code_count(self, pattern: Pattern, metacode: str) -> int:
        """should only be called for test purposes or if not used frequently,
        because the computation is not very efficient
        """
        ...

    def get_pattern_metacode_counter(
            self) -> Dict[Pattern, Dict[Set[Metacode], Dict[Metacode, int]]]:
        ...

    def start_trace_covering(self, trace: Tuple):
        """signal that now the given trace starts to get covered"""
        ...

    def end_trace_covering(self, trace: Tuple):
        """signal that now the given trace is get covered"""
        ...

    def use_cache_to_cover_trace(self, trace: Tuple[str]):
        """repeats the addition of codes as it is stored in a cache for the
        same sequence of activities as the given trace"""
        ...
