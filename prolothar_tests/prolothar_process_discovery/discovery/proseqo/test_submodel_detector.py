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
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.submodel_detector import SubmodelDetector
from prolothar_process_discovery.discovery.proseqo.clustering.spectral_clustering import SpectralClustering
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.activity_set_similarity import ActivitySetSimilarity
from prolothar_common.collections import set_similarity

from prolothar_process_discovery.data.synthetic_baking import baking

class TestSubmodelDetector(unittest.TestCase):

    def test_on_baking_log(self):
        log = baking.generate_log(100, use_clustering_model=True)
        pattern_dfg = PatternDfg.create_from_event_log(log)
        submodel_detector = SubmodelDetector([
                SpectralClustering(
                        2, ActivitySetSimilarity(set_similarity.jaccard_index)),
                SpectralClustering(
                        3, ActivitySetSimilarity(set_similarity.jaccard_index))])
        new_pattern_dfg, partitions = submodel_detector.detect(
                pattern_dfg, log, verbose=False)
        self.assertEqual(4, new_pattern_dfg.get_nr_of_nodes())
        self.assertTrue(6 <= len(partitions) <= 8)

if __name__ == '__main__':
    unittest.main()