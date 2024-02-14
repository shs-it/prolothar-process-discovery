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

cdef class CoveringSingleton(CoveringPattern):

    def __init__(self, object singleton, object trace, str last_covered_activity):
        super().__init__(singleton, trace, last_covered_activity)

    cpdef process_covering_step(self, cover, str last_activity, str next_activity):
        if self.completed_covering:
            raise ValueError('Singleton already has been used for covering')
        cover.move_stream.add_synchronous_move(last_activity)
        self.started_covering = True
        self.completed_covering = True

    cpdef int skip_to_end(self, object cover, object trace, str last_covered_activity):
        if not self.completed_covering:
            cover.move_stream.add_model_move(last_covered_activity)
        self.started_covering = True
        self.completed_covering = True
        return 1

    cdef set _get_next_coverable_activities(self):
        raise NotImplementedError('should not be called on singletons')

    cpdef bint can_cover(self, str activity):
        return (not self.completed_covering and
                self.pattern.contains_activity(activity))
