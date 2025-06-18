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
from typing import Tuple, Dict, List
from prolothar_common cimport mdl_utils

cdef str SYNCHRONOUS_MOVE = 'sync'
cdef str LOG_MOVE = 'log'
cdef str MODEL_MOVE = 'model'

cdef class MoveStream():
    """code stream of the cover that stores codes for model moves, log moves
    and synchronous moves. model moves are activities in the
    model that are not observable in the log. a log move is an activity that
    is observed in the log but not explained by the model. a synchronous move
    is behavior that is both modeled and observed"""

    SYNCHRONOUS_MOVE = 'sync'
    LOG_MOVE = 'log'
    MODEL_MOVE = 'model'

    def __init__(self):
        """creates a new, empty move stream"""
        self.__conditional_counter = {}
        self.__trace_move_codes_cache = {}

    cpdef MoveStream copy_counts_only(self):
        """returns a copy of this stream. Only the counts are copied.
        All caches and any other information is not copied
        """
        cdef MoveStream copy = MoveStream()
        copy.__conditional_counter = {}
        for context, move_stream_counter in self.__conditional_counter.items():
            copy.__conditional_counter[context] = dict(move_stream_counter)
        return copy

    cpdef add_log_move(self, str last_covered_activity, int count = 1,
                       bint add_to_cache = True):
        """adds the code for a log move to this stream

        Args:
            last_covered_activity:
                used to compute the conditional probability of observing
                a log move. can be None at the beginning of a trace
            count:
                default is 1.
        """
        self.__add_move_code(
                last_covered_activity, LOG_MOVE, count,
                add_to_cache=add_to_cache)

    cpdef add_model_move(self, str last_covered_activity, int count = 1,
                         bint add_to_cache = True):
        """adds the code for a model move to this stream
        Args:
            last_covered_activity:
                used to compute the conditional probability of observing
                a model move. can be None at the beginning of a trace
            count:
                default is 1.
        """
        self.__add_move_code(
                last_covered_activity, MODEL_MOVE, count,
                add_to_cache=add_to_cache)

    cpdef add_synchronous_move(self, str last_covered_activity, int count = 1,
                               bint add_to_cache = True):
        """adds the code for a synchronous move to this stream

        Args:
            last_covered_activity:
                used to compute the conditional probability of observing
                a sync move. can be None at the beginning of a trace
            count:
                default is 1.
        """
        self.__add_move_code(
                last_covered_activity, SYNCHRONOUS_MOVE, count,
                add_to_cache=add_to_cache)

    cdef __add_move_code(
            self, str last_covered_activity, str move_code, int count,
            bint add_to_cache = True):
        cdef dict counter = <dict>self.__conditional_counter.get(last_covered_activity, None)
        if counter is None:
            counter = {
                    SYNCHRONOUS_MOVE: 0,
                    MODEL_MOVE: 0,
                    LOG_MOVE: 0,
            }
            self.__conditional_counter[last_covered_activity] = counter
        counter[move_code] += count
        if add_to_cache:
            (<list>self.__trace_move_codes_cache[self.__current_trace]).append(
                    (last_covered_activity, move_code))

    def flip_moves(self, last_covered_activity: str, from_code: str,
                   to_code: str, amount: int = -1):
        """in context of the given last_covered_activity, turn "amount" many
        "from_code"s into "to_code"s. This function will set amount to the existing
        count if amount is larger than that to ensure non-negative counts.
        """
        #if the given activity is for example always the last one, then it is
        #not in the counter
        if last_covered_activity in self.__conditional_counter:
            move_counter = self.__conditional_counter[last_covered_activity]
            if amount < 0:
                amount = move_counter[from_code]
            else:
                amount = min(move_counter[from_code], amount)
            move_counter[from_code] -= amount
            move_counter[to_code] += amount

    def decrease_count(self, last_covered_activity: str, move_code: str,
                       amount: int):
        """in context of the given last_covered_activity, decreases the count
        of the given move_code. The function ensures that there is no negative
        count after its call.
        """
        #if the given activity is for example always the last one, then it is
        #not in the counter
        if last_covered_activity in self.__conditional_counter:
            count = self.__conditional_counter[last_covered_activity][move_code]
            count = max(0, count - amount)
            self.__conditional_counter[last_covered_activity][move_code] = count

    def remove_last_move(self):
        context,move = self.__trace_move_codes_cache[self.__current_trace].pop()
        self.__conditional_counter[context][move] -= 1

    def get_encoded_length(self, verbose=False) -> float:
        """retuns the MDL of this stream. this does not include the length of the
        stream because this is explicitly known by the number of traces and
        length of the traces that is encoded in the cover"""
        encoded_length = 0
        for counter in self.__conditional_counter.values():
            encoded_length += mdl_utils.prequential_coding_length(counter)

        if verbose:
            print('encoded length of move stream: %.2f' % encoded_length)
            print(self.count_move_codes())

        return encoded_length

    def count_move_codes(self) -> Dict[str, int]:
        """returns a dictionary that stores for each move code how many
        times it has been used in total
        """
        cdef dict total_counter = {
            SYNCHRONOUS_MOVE: 0,
            MODEL_MOVE: 0,
            LOG_MOVE: 0,
        }
        for counter in self.__conditional_counter.values():
            for code,count in counter.items():
                total_counter[code] += count
        return total_counter

    def get_number_of_synchronous_moves(self) -> int:
        return self.count_move_codes()[SYNCHRONOUS_MOVE]

    def get_number_of_log_moves(self) -> int:
        return self.count_move_codes()[LOG_MOVE]

    def get_number_of_model_moves(self) -> int:
        return self.count_move_codes()[MODEL_MOVE]

    def start_trace_covering(self, tuple trace):
        """signal that now the given trace starts to get covered"""
        self.__current_trace = trace
        self.__trace_move_codes_cache[trace] = []

    def end_trace_covering(self, tuple trace):
        """signal that now the given trace is covered"""
        self.__current_trace = None

    def use_cache_to_cover_trace(self, trace: Tuple[str]):
        """repeats the addition of codes as it is stored in a cache for the
        same sequence of activities as the given trace"""
        for move_code in self.__trace_move_codes_cache[trace]:
            self.__add_move_code((<tuple>move_code)[0], (<tuple>move_code)[1], 1, add_to_cache=False)

    def get_move_codes_cache(self) -> Dict[Tuple[str], List[Tuple[str]]]:
        """
        provides the trace cache for move codes. the returned dictionary should
        not be changed!
        Returns
        -------
        Dict[Tuple[str], List[Tuple[str]]]
            for a given trace stores a sequence of move codes
            (last_covery_activity,move_code).
        """
        return self.__trace_move_codes_cache