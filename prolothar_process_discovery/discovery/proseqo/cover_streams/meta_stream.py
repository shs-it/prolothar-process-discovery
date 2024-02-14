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
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import Pattern
from prolothar_common.models.eventlog import Trace
from typing import List, Union, Tuple, Dict, Set
from prolothar_common import mdl_utils

Metacode = Union[Pattern,str]
class MetaStream:
    def __init__(self):
        self.__pattern_meta_code_conditional_counter = {}
        self.__trace_metacodes_cache = {}

    def copy_counts_only(self) -> 'MetaStream':
        """returns a copy of this stream. Only the counts are copied.
        All caches and any other information is not copied
        """
        copy = MetaStream()

        copy.__pattern_meta_code_conditional_counter = {}
        for pattern, conditional_metacode_counter in \
        self.__pattern_meta_code_conditional_counter.items():
            copy_of_meta_code_conditional_counter = {}
            copy.__pattern_meta_code_conditional_counter[pattern] = \
                copy_of_meta_code_conditional_counter
            for pattern, last_activity_counter in conditional_metacode_counter.items():
                copy_of_last_activity_counter = {}
                copy_of_meta_code_conditional_counter[
                        pattern] = copy_of_last_activity_counter
                for context, metacode_counter in last_activity_counter.items():
                    copy_of_last_activity_counter[context] = dict(metacode_counter)
        return copy

    def __add_metacode(self, pattern: Pattern, metacode: str,
                       possible_metacodes: List[str],
                       last_covered_activity: str,
                       add_to_cache: bool = True):
        if pattern.get_activity_name() not in self.__pattern_meta_code_conditional_counter:
            self.__pattern_meta_code_conditional_counter[
                    pattern.get_activity_name()] = {}
        conditional_metacode_counter = \
            self.__pattern_meta_code_conditional_counter[pattern.get_activity_name()]
        if last_covered_activity not in conditional_metacode_counter:
            conditional_metacode_counter[last_covered_activity] = {}
        conditional_metacode_counter = conditional_metacode_counter[
                last_covered_activity]
        if possible_metacodes not in conditional_metacode_counter:
            conditional_metacode_counter[possible_metacodes] = {
                alternative: 0 for alternative in possible_metacodes
            }
        conditional_metacode_counter[possible_metacodes][metacode] += 1
        if add_to_cache:
            self.__trace_metacodes_cache[self.__current_trace].append(
                    (pattern, metacode, possible_metacodes,
                     last_covered_activity))

    def add_present_code(self, pattern: Pattern, last_covered_activity: str):
        """adds a "present" meta code"""
        self.__add_metacode(pattern, 'present', frozenset(['present', 'absent']),
                            last_covered_activity)

    def add_absent_code(self, pattern: Pattern, last_covered_activity: str):
        """adds a "absent" meta code"""
        self.__add_metacode(pattern, 'absent', frozenset(['present', 'absent']),
                            last_covered_activity)

    def add_repeat_code(self, pattern: Pattern, iteration: int,
                        last_covered_activity: str):
        """adds a "repeat" meta code"""
        self.__add_metacode(
                pattern, 'repeat%d' % iteration,
                frozenset(['repeat%d' % iteration, 'end%d' % iteration]),
                last_covered_activity)

    def add_end_code(self, pattern: Pattern, iteration: int,
                     last_covered_activity: str):
        """adds an "end" meta code"""
        self.__add_metacode(
                pattern, 'end%d' % iteration,
                frozenset(['repeat%d' % iteration, 'end%d' % iteration]),
                last_covered_activity)

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
        self.__add_metacode(pattern, subpattern, subpattern_alternatives,
                            last_covered_activity)

    def get_code_length(self, verbose=False) -> float:
        """returns the code length of this meta stream using optimal prefix codes"
        """
        code_length = 0

        for metacode_conditional_counter in \
            self.__pattern_meta_code_conditional_counter.values():
                for pattern_metacode_counter in metacode_conditional_counter.values():
                    for metacode_counter in pattern_metacode_counter.values():
                        code_length += mdl_utils.prequential_coding_length(
                                metacode_counter)

        if verbose:
            print('encoded length of meta stream: %.2f' % code_length)

        return code_length

    def get_code_count(self, pattern: Pattern, metacode: str) -> int:
        """should only be called for test purposes or if not used frequently,
        because the computation is not very efficient
        """
        code_count = 0
        for pattern_metacode_counter in \
        self.__pattern_meta_code_conditional_counter[
                pattern.get_activity_name()].values():
            for meta_code_counter in pattern_metacode_counter.values():
                code_count += meta_code_counter.get(metacode, 0)
        return code_count

    def get_pattern_metacode_counter(
            self) -> Dict[Pattern, Dict[Set[Metacode], Dict[Metacode, int]]]:
        return self.__pattern_meta_code_conditional_counter

    def start_trace_covering(self, trace: Trace):
        """signal that now the given trace starts to get covered"""
        self.__current_trace = trace
        self.__trace_metacodes_cache[self.__current_trace] = []

    def end_trace_covering(self, trace: Trace):
        """signal that now the given trace is get covered"""
        self.__current_trace = None

    def use_cache_to_cover_trace(self, trace: Tuple[str]):
        """repeats the addition of codes as it is stored in a cache for the
        same sequence of activities as the given trace"""
        for pattern, metacode, possible_metacodes, last_covered_activity in \
        self.__trace_metacodes_cache[trace]:
            self.__add_metacode(pattern, metacode, possible_metacodes,
                                last_covered_activity, add_to_cache=False)
