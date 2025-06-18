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
from prolothar_common.models.eventlog.trace cimport Trace
from prolothar_common cimport mdl_utils

cdef class MetaStream:
    def __init__(self):
        self.__pattern_meta_code_conditional_counter = {}
        self.__trace_metacodes_cache = {}
        self.__present_code = 'present'
        self.__absent_code = 'absent'
        self.__present_absent_codes = frozenset([self.__present_code, self.__absent_code])

    cpdef MetaStream copy_counts_only(self):
        """returns a copy of this stream. Only the counts are copied.
        All caches and any other information is not copied
        """
        cdef MetaStream copy = MetaStream()
        copy.__pattern_meta_code_conditional_counter = {}
        for pattern, conditional_metacode_counter in \
        self.__pattern_meta_code_conditional_counter.items():
            copy_of_meta_code_conditional_counter = {}
            copy.__pattern_meta_code_conditional_counter[pattern] = \
                copy_of_meta_code_conditional_counter
            for pattern, last_activity_counter in (<dict>conditional_metacode_counter).items():
                copy_of_last_activity_counter = {}
                copy_of_meta_code_conditional_counter[pattern] = copy_of_last_activity_counter
                for context, metacode_counter in (<dict>last_activity_counter).items():
                    copy_of_last_activity_counter[context] = dict(metacode_counter)
        return copy

    cdef __add_metacode(self, Pattern pattern, str metacode,
                       frozenset possible_metacodes,
                       str last_covered_activity,
                       bint add_to_cache = True):
        if pattern.get_activity_name() not in self.__pattern_meta_code_conditional_counter:
            self.__pattern_meta_code_conditional_counter[pattern.get_activity_name()] = {}
        conditional_metacode_counter = self.__pattern_meta_code_conditional_counter[pattern.get_activity_name()]
        if last_covered_activity not in conditional_metacode_counter:
            conditional_metacode_counter[last_covered_activity] = {}
        conditional_metacode_counter = conditional_metacode_counter[last_covered_activity]
        if possible_metacodes not in conditional_metacode_counter:
            conditional_metacode_counter[possible_metacodes] = {
                alternative: 0 for alternative in possible_metacodes
            }
        conditional_metacode_counter[possible_metacodes][metacode] += 1
        if add_to_cache:
            (<list>self.__trace_metacodes_cache[self.__current_trace]).append(
                (pattern, metacode, possible_metacodes, last_covered_activity)
            )

    cpdef add_present_code(self, Pattern pattern, str last_covered_activity):
        """adds a "present" meta code"""
        self.__add_metacode(pattern, self.__present_code, self.__present_absent_codes, last_covered_activity)

    cpdef add_absent_code(self, Pattern pattern, str last_covered_activity):
        """adds a "absent" meta code"""
        self.__add_metacode(pattern, self.__absent_code, self.__present_absent_codes, last_covered_activity)

    cpdef add_repeat_code(self, Pattern pattern, int iteration, str last_covered_activity):
        """adds a "repeat" meta code"""
        self.__add_metacode(
            pattern, 
            'repeat%d' % iteration,
            frozenset(['repeat%d' % iteration, 'end%d' % iteration]),
            last_covered_activity
        )

    cpdef add_end_code(self, Pattern pattern, int iteration, str last_covered_activity):
        """adds an "end" meta code"""
        self.__add_metacode(
            pattern, 
            'end%d' % iteration,
            frozenset(['repeat%d' % iteration, 'end%d' % iteration]),
            last_covered_activity
        )

    cpdef add_routing_code(
        self, Pattern pattern, 
        Pattern subpattern,
        frozenset subpattern_alternatives,
        str last_covered_activity):
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
        self.__add_metacode(pattern, subpattern.get_activity_name(), subpattern_alternatives, last_covered_activity)

    cpdef add_routing_code_for_given_activity(
            self, Pattern pattern, 
            str next_activity,
            frozenset activity_alternatives,
            str last_covered_activity):
        self.__add_metacode(pattern, next_activity, activity_alternatives, last_covered_activity)     

    cpdef float get_code_length(self, bint verbose=False):
        """returns the code length of this meta stream using optimal prefix codes"
        """
        cdef float code_length = 0

        for metacode_conditional_counter in self.__pattern_meta_code_conditional_counter.values():
                for pattern_metacode_counter in (<dict>metacode_conditional_counter).values():
                    for metacode_counter in (<dict>pattern_metacode_counter).values():
                        code_length += mdl_utils.prequential_coding_length(<dict>metacode_counter)

        if verbose:
            print('encoded length of meta stream: %.2f' % code_length)

        return code_length

    cpdef int get_code_count(self, Pattern pattern, str metacode):
        """should only be called for test purposes or if not used frequently,
        because the computation is not very efficient
        """
        cdef int code_count = 0
        for pattern_metacode_counter in (<dict>self.__pattern_meta_code_conditional_counter[pattern.get_activity_name()]).values():
            for meta_code_counter in (<dict>pattern_metacode_counter).values():
                code_count += <int>(<dict>meta_code_counter).get(metacode, 0)
        return code_count

    cpdef dict get_pattern_metacode_counter(self):
        return self.__pattern_meta_code_conditional_counter

    cpdef start_trace_covering(self, tuple trace):
        """signal that now the given trace starts to get covered"""
        self.__current_trace = trace
        self.__trace_metacodes_cache[self.__current_trace] = []

    cpdef end_trace_covering(self, tuple trace):
        """signal that now the given trace is get covered"""
        self.__current_trace = None

    cpdef use_cache_to_cover_trace(self, tuple trace):
        """repeats the addition of codes as it is stored in a cache for the
        same sequence of activities as the given trace"""
        for pattern, metacode, possible_metacodes, last_covered_activity in \
        self.__trace_metacodes_cache[trace]:
            self.__add_metacode(pattern, metacode, possible_metacodes,
                                last_covered_activity, add_to_cache=False)
