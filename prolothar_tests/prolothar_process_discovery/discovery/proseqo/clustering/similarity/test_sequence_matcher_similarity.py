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
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.sequence_matcher_similarity import SequenceMatcherSimilarity
from prolothar_common.models.eventlog import EventLog

class TestSequenceMatcherSimilarity(unittest.TestCase):

    def setUp(self):
        self.log1 = EventLog.create_from_simple_activity_log([
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','1','2','6'],
        ])
        self.log2 = EventLog.create_from_simple_activity_log([
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','7','2','6'],
            ['0','1','2','4','5','1','2','6'],
            ['0','7','8','6']
        ])
        self.log3 = EventLog.create_from_simple_activity_log([
            ['A','B','C'],
            ['A','B','D'],
        ])

        self.log4 = EventLog.create_from_simple_activity_log([
           ['Start', 'Add Eggs', 'Add Sugar', 'Beat up Foamy', 'Add Flour',
            'Fold in', 'Put into Oven']
        ])
        self.log5 = EventLog.create_from_simple_activity_log([
           ['Start', 'Add Milk', 'Add Sugar', 'Add Yeast', 'Stir in Flour',
            'Put into Oven']
        ])


    def test_compute_on_two_traces(self):
        log1 = EventLog.create_from_simple_activity_log([
            list('THANKS FOR RESPONSE')
        ])
        log2 = EventLog.create_from_simple_activity_log([
            list('THANKING FOR KIND RESPONSE')
        ])
        similarity = SequenceMatcherSimilarity()
        similarity.precompute([log1, log2])
        self.assertEqual(0.8, similarity.compute(log1, log2))

    def test_compute_on_logs(self):
        similarity = SequenceMatcherSimilarity()
        similarity.precompute([self.log1, self.log2, self.log3, self.log4,
                               self.log5])
        self.assertEqual(1.0, similarity.compute(self.log1, self.log1))
        self.assertEqual(1.0, similarity.compute(self.log2, self.log2))
        self.assertEqual(1.0, similarity.compute(self.log3, self.log3))

        self.assertAlmostEqual(0.767, similarity.compute(self.log1, self.log2),
                               delta=0.001)
        self.assertAlmostEqual(0.661, similarity.compute(self.log4, self.log5),
                               delta=0.001)

        self.assertEqual(0.0, similarity.compute(self.log1, self.log3))
        self.assertEqual(0.0, similarity.compute(self.log2, self.log3))

if __name__ == '__main__':
    unittest.main()
