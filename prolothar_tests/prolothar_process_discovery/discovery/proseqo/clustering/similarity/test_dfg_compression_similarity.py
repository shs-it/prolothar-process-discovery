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
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.dfg_compression_similarity import DfgCompressionSimilarity
from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_size.nr_of_nodes import NrOfNodes
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_size.nr_of_edges import NrOfEdges
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_size.sum_of import SumOf
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_size.average_degree import AverageDegree
from prolothar_process_discovery.discovery.proseqo.pattern_dfg_size.model_mdl import ModelMdl

class TestDfgCompressionSimilarity(unittest.TestCase):

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

    def test_nr_of_nodes(self):
        similarity = DfgCompressionSimilarity(NrOfNodes())
        similarity.precompute([self.log1, self.log2, self.log3, self.log4,
                               self.log5])
        self.assertEqual(1.0, similarity.compute(self.log1, self.log1))
        self.assertEqual(1.0, similarity.compute(self.log2, self.log2))
        self.assertEqual(1.0, similarity.compute(self.log3, self.log3))

        self.assertEqual(0.75, similarity.compute(self.log1, self.log2))
        self.assertAlmostEqual(0.429, similarity.compute(self.log4, self.log5),
                               delta=0.001)

        self.assertEqual(0.0, similarity.compute(self.log1, self.log3))
        self.assertEqual(0.0, similarity.compute(self.log2, self.log3))

    def test_nr_of_with_compression(self):
        similarity = DfgCompressionSimilarity(
                NrOfNodes(), compress_pattern_dfg = True)
        similarity.precompute([self.log1, self.log2, self.log3, self.log4,
                               self.log5])
        self.assertEqual(1.0, similarity.compute(self.log1, self.log1))
        self.assertEqual(1.0, similarity.compute(self.log2, self.log2))
        self.assertEqual(1.0, similarity.compute(self.log3, self.log3))

        self.assertAlmostEqual(0.571, similarity.compute(self.log1, self.log2),
                               delta=0.001)
        self.assertAlmostEqual(1, similarity.compute(self.log4, self.log5),
                               delta=0.001)

        self.assertEqual(0.0, similarity.compute(self.log1, self.log3))
        self.assertEqual(0.0, similarity.compute(self.log2, self.log3))

    def test_model_mdl_compression(self):
        similarity = DfgCompressionSimilarity(
                ModelMdl(), compress_pattern_dfg = True)
        similarity.precompute([self.log1, self.log2, self.log3, self.log4,
                               self.log5])
        self.assertEqual(1.0, similarity.compute(self.log1, self.log1))
        self.assertEqual(1.0, similarity.compute(self.log2, self.log2))
        self.assertEqual(1.0, similarity.compute(self.log3, self.log3))

        self.assertAlmostEqual(0.679, similarity.compute(self.log1, self.log2),
                               delta=0.001)
        self.assertAlmostEqual(-0.022, similarity.compute(self.log4, self.log5),
                               delta=0.001)

        self.assertAlmostEqual(-0.182, similarity.compute(self.log1, self.log3),
                               delta=0.001)
        self.assertAlmostEqual(-0.141, similarity.compute(self.log2, self.log3),
                               delta=0.001)

    def test_nr_of_edges_nodes(self):
        similarity = DfgCompressionSimilarity(SumOf([
                NrOfNodes(), NrOfEdges()]))
        similarity.precompute([self.log1, self.log2, self.log3, self.log4,
                               self.log5])

        self.assertEqual(0.65, similarity.compute(self.log1, self.log2))
        self.assertEqual(1.0, similarity.compute(self.log4, self.log4))
        self.assertEqual(1.0, similarity.compute(self.log5, self.log5))
        self.assertAlmostEqual(0.23, similarity.compute(self.log4, self.log5),
                               delta=0.001)

    def test_average_degree(self):
        similarity = DfgCompressionSimilarity(AverageDegree())
        similarity.precompute([self.log1, self.log2, self.log3, self.log4,
                               self.log5])

        self.assertEqual(1.0, similarity.compute(self.log1, self.log1))
        self.assertEqual(1.0, similarity.compute(self.log2, self.log2))
        self.assertEqual(1.0, similarity.compute(self.log3, self.log3))

        self.assertAlmostEqual(0.777, similarity.compute(self.log1, self.log2),
                               delta=0.001)
        self.assertAlmostEqual(0.688, similarity.compute(self.log4, self.log5),
                               delta=0.001)

        self.assertAlmostEqual(0.786, similarity.compute(self.log1, self.log3),
                               delta=0.001)
        self.assertAlmostEqual(0.666, similarity.compute(self.log2, self.log3),
                               delta=0.001)

if __name__ == '__main__':
    unittest.main()
