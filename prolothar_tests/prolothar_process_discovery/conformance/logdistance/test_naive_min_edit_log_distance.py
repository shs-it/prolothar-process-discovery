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

import unittest
from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.conformance.logdistance.naive_min_edit_distance import NaiveMinEditLogDistance

class TestGreedyMinEditDistance(unittest.TestCase):

    def test_compute_no_distance(self):
        log1 = EventLog.create_from_simple_activity_log([
            [0,0,0,1,2,3,4,5,4,5,6],
            [0,0,1,3,2,4,5,4,5,6],
        ])
        self.assertEqual(0, NaiveMinEditLogDistance().compute(log1,log1))

    def test_compute_two_removes(self):
        log1 = EventLog.create_from_simple_activity_log([
            [0,0,0,1,2,3,4,5,4,5,6],
            [0,0,1,3,2,4,5,4,5,6],
        ])
        log2 = EventLog.create_from_simple_activity_log([
            [0,0,0,1,2,3,4,5,5,6],
            [0,0,1,2,4,5,4,5,6],
        ])
        self.assertEqual(2, NaiveMinEditLogDistance().compute(log1,log2))


if __name__ == '__main__':
    unittest.main()