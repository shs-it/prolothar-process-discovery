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
from prolothar_process_discovery.discovery.proseqo.edge_removal.no_removal import NoRemoval
from prolothar_process_discovery.discovery.proseqo.edge_removal.mdl_greedy import MdlGreedy
from prolothar_process_discovery.discovery.proseqo.edge_removal.mdl_greedy_2 import MdlGreedy2
from prolothar_process_discovery.discovery.proseqo.edge_removal.mdl_local_edge_frequency import MdlLocalEdgeFrequency
from prolothar_process_discovery.discovery.proseqo.edge_removal.mdl_lowest_loss import MdlLowestLoss
from prolothar_process_discovery.discovery.proseqo.edge_removal.termination_criterion import MaxNumberOfEdgesRemoved
from prolothar_process_discovery.discovery.proseqo.edge_removal.termination_criterion import MaxGraphDensityReached
from prolothar_process_discovery.discovery.proseqo.edge_removal.probabilistic import Probabilistic
from prolothar_process_discovery.discovery.proseqo.edge_removal.mst import MinimumSpanningTree
from prolothar_process_discovery.discovery.proseqo.edge_removal.event_recall_edge_pruning import EventRecallEdgePruning
from prolothar_common.models.eventlog import EventLog

class TestEventRecallEdgePruning(unittest.TestCase):

    def setUp(self):
        simple_activity_log = []
        for i in range(100):
            simple_activity_log.append(['0', '1', '2', '3'])
        simple_activity_log.append(['0', '2', '1', '3'])
        self.log = EventLog.create_from_simple_activity_log(
                simple_activity_log)

        self.dfg = PatternDfg.create_from_event_log(self.log)

    def test_no_removal(self):
        self.assertEqual(self.dfg, NoRemoval().remove_edges(self.dfg, self.log))

    def test_mdl_greedy(self):
        folded_dfg = MdlGreedy().remove_edges(self.dfg, self.log)
        self.assertEqual(2, folded_dfg.get_nr_of_nodes())
        self.assertEqual(1, folded_dfg.get_nr_of_edges())

    def test_mdl_greedy_2(self):
        folded_dfg = MdlGreedy2().remove_edges(self.dfg, self.log)
        self.assertEqual(4, folded_dfg.get_nr_of_nodes())
        self.assertEqual(3, folded_dfg.get_nr_of_edges())

    def test_mdl_local_edge_frequency(self):
        folded_dfg = MdlLocalEdgeFrequency([0.001, 0.02, 1.0]).remove_edges(
                self.dfg, self.log)
        self.assertEqual(4, folded_dfg.get_nr_of_nodes())
        self.assertEqual(3, folded_dfg.get_nr_of_edges())

    def test_mdl_lowest_loss_remove_n_edges(self):
        folded_dfg = MdlLowestLoss(MaxNumberOfEdgesRemoved(2)).remove_edges(
                self.dfg, self.log, verbose=True)
        self.assertEqual(4, folded_dfg.get_nr_of_nodes())
        self.assertEqual(4, folded_dfg.get_nr_of_edges())

    def test_mdl_lowest_loss_graph_density_threshold(self):
        folded_dfg = MdlLowestLoss(MaxGraphDensityReached(0.3)).remove_edges(
                self.dfg, self.log, verbose=True)
        self.assertEqual(4, folded_dfg.get_nr_of_nodes())
        self.assertEqual(4, folded_dfg.get_nr_of_edges())

    def test_probabilistic(self):
        folded_dfg = Probabilistic().remove_edges(
                self.dfg, self.log)
        self.assertEqual(4, folded_dfg.get_nr_of_nodes())
        self.assertEqual(3, folded_dfg.get_nr_of_edges())

    def test_minimum_spanning_tree(self):
        folded_dfg = MinimumSpanningTree(0.02).remove_edges(
                self.dfg, self.log)
        self.assertEqual(4, folded_dfg.get_nr_of_nodes())
        self.assertEqual(3, folded_dfg.get_nr_of_edges())

    def test_event_recall_edge_pruning(self):
        folded_dfg = EventRecallEdgePruning(0.9).remove_edges(
                self.dfg, self.log, verbose=True)
        self.assertEqual(4, folded_dfg.get_nr_of_nodes())
        self.assertEqual(3, folded_dfg.get_nr_of_edges())


if __name__ == '__main__':
    unittest.main()