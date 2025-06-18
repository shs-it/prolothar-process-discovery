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
from prolothar_process_discovery.discovery.proseqo.pattern.pattern cimport Pattern
from typing import List, Dict, FrozenSet
from prolothar_common cimport mdl_utils

cdef class PatternStream:
    """pattern stream of cover, i.e. a stream of patterns that is used to
    cover (= encode) a set of sequences"""

    def __init__(self, store_patterns=False):
        """creates a new pattern stream.

        Args:
            possible_patterns:
                A list of patterns that can be present in the pattern stream.
                this is needed to initialize the prequential codes to uniform
                probability.
            store_patterns:
                default is False. If true, the patterns in the
                stream are explicitly stored in memory when "add" is called.
                This is useful, if one really needs to know the sequence of the
                added patterns
        """
        self._usage_per_pattern_conditional = {}
        self._store_patterns = store_patterns
        self._pattern_sequence = []
        self.__pattern_sequence_cache = {}

    cpdef PatternStream copy_counts_only(self):
        """returns a copy of this stream. Only the counts are copied.
        All caches and any other information is not copied
        """
        cdef PatternStream copy = PatternStream()
        cdef dict copy_of_pattern_usage_dict
        copy._usage_per_pattern_conditional = {}
        for context, pattern_usage_dict in self._usage_per_pattern_conditional.items():
            copy_of_pattern_usage_dict = {}
            copy._usage_per_pattern_conditional[context] = copy_of_pattern_usage_dict
            for pattern, usage in (<dict>pattern_usage_dict).items():
                copy_of_pattern_usage_dict[pattern] = usage
        return copy

    cpdef add(self, Pattern pattern, frozenset usable_pattern_activities,
            bint add_to_cache = True, int count = 1):
        """adds a pattern code to this stream
        Args:
            pattern:
                the pattern that is used for encoding the data and is added
                to this stream. must be in the list of possible patterns that
                has been given to the constructor. otherwise the computed
                code length will be wrong.
            usable_pattern_activities:
                gives the activity names of all patterns that could have been
                used at this stage - inclusive the pattern that has been used
            add_to_cache:
                has only internal usage and should not be used by other classes
        """
        if not usable_pattern_activities:
            raise ValueError('usable_pattern_activities must not be empty')
        if add_to_cache:
            self.__current_trace_cache.append(
                    (pattern, usable_pattern_activities))
        if self._store_patterns:
            self._pattern_sequence.append(pattern)
        cdef frozenset conditional
        cdef dict usage_per_pattern = <dict>self._usage_per_pattern_conditional.get(usable_pattern_activities, None)
        if usage_per_pattern is None:
            usage_per_pattern = dict.fromkeys(usable_pattern_activities, 0)
            self._usage_per_pattern_conditional[usable_pattern_activities] = usage_per_pattern
        usage_per_pattern[pattern.get_activity_name()] += count

    cpdef remove(self, Pattern pattern, frozenset usable_pattern_activities,
                 int count = 1):
        """removes counts from this pattern stream"""
        self._usage_per_pattern_conditional[
                frozenset(usable_pattern_activities)][
                        pattern.get_activity_name()] -= count

    cpdef remove_pattern_from_context(
            self, frozenset context, Pattern pattern):
        cdef dict pattern_count_dict = self._usage_per_pattern_conditional.pop(context)
        pattern_count_dict.pop(pattern.get_activity_name())
        new_context = context.difference([pattern.get_activity_name()])
        self._usage_per_pattern_conditional[new_context] = pattern_count_dict

    cpdef float get_code_length(self, bint verbose=False):
        """
        Returns:
            the encoded length of this pattern stream
        """
        cdef float code_length = 0.0

        for pattern_counter in self._usage_per_pattern_conditional.values():
            code_length += mdl_utils.prequential_coding_length(<dict>pattern_counter)

        if verbose:
            print('encoded length of pattern stream: %.2f' % code_length)

        return code_length

    def get_sequence_of_added_patterns(self) -> List[Pattern]:
        """returns a list with all patterns added to the stream. the order
        is the same as they have been added to stream. if a patterns has been
        added multiple times to the stream it will occur multiple times in this
        list.

        Raises:
            ValueError:
                if the pattern stream was not iniatialized with
                "store_patterns=True"
        """
        if not self._store_patterns:
            raise ValueError()
        return self._pattern_sequence

    def get_usage_per_pattern(self) -> Dict[str, int]:
        """returns a dict with activity name => total usage"""
        cdef dict usage_per_pattern = {}
        for pattern_usage_dict in self._usage_per_pattern_conditional.values():
            for pattern, usage in pattern_usage_dict.items():
                try:
                    usage_per_pattern[pattern] += usage
                except KeyError:
                    usage_per_pattern[pattern] = usage
        return usage_per_pattern

    def get_conditional_usage_per_pattern(
            self) -> Dict[FrozenSet[str], Dict[str, int]]:
        """returns a nested dictionary (alternative patterns) -> pattern -> count
        """
        return self._usage_per_pattern_conditional

    cpdef start_trace_covering(self, tuple trace):
        """signal that now the given trace starts to get covered"""
        self.__current_trace = trace
        self.__current_trace_cache = []
        self.__pattern_sequence_cache[self.__current_trace] = self.__current_trace_cache

    cpdef end_trace_covering(self, tuple trace):
        """signal that now the given trace is get covered"""
        self.__current_trace = None
        self.__current_trace_cache = None

    cpdef use_cache_to_cover_trace(self, tuple trace):
        """repeats the addition of codes as it is stored in a cache for the
        same sequence of activities as the given trace"""
        for pattern, usable_pattern_activities in self.__pattern_sequence_cache[trace]:
            self.add(<Pattern>pattern, <frozenset>usable_pattern_activities, add_to_cache=False)
