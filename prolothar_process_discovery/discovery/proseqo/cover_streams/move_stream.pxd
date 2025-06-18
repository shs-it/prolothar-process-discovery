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

cdef class MoveStream():
    """code stream of the cover that stores codes for model moves, log moves
    and synchronous moves. model moves are activities in the
    model that are not observable in the log. a log move is an activity that
    is observed in the log but not explained by the model. a synchronous move
    is behavior that is both modeled and observed"""

    cdef dict __conditional_counter
    cdef dict __trace_move_codes_cache
    cdef tuple __current_trace

    cpdef MoveStream copy_counts_only(self)

    cpdef add_log_move(self, str last_covered_activity, int count = ?,
                       bint add_to_cache = ?)

    cpdef add_model_move(self, str last_covered_activity, int count = ?,
                         bint add_to_cache = ?)

    cpdef add_synchronous_move(self, str last_covered_activity, int count = ?,
                               bint add_to_cache = ?)

    cdef __add_move_code(
            self, str last_covered_activity, str move_code, int count,
            bint add_to_cache = ?)


