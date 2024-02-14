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
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_common.models.data_petri_net import DataPetriNet

class TestSubgraph(unittest.TestCase):

    def test_create_cutlog_from_community(self):
        pattern_dfg = PatternDfg()
        pattern_dfg.add_count('A','B')
        pattern_dfg.add_count('B','C')

        log = EventLog.create_from_simple_activity_log([
            ['0','A','B','C','1']
        ])

        subgraph = SubGraph(pattern_dfg,
                            pattern_dfg.get_source_activities(),
                            pattern_dfg.get_sink_activities())

        cutlog = subgraph.create_cut_log_from_community(log)

        expected_cutlog = EventLog.create_from_simple_activity_log([
            ['A','B','C']
        ])

        self.assertEqual(expected_cutlog, cutlog)

    def test_add_to_petri_net(self):
        petri_net = DataPetriNet()

        pattern_dfg = PatternDfg()
        pattern_dfg.add_count('A','B')
        pattern_dfg.add_count('B','C')
        subgraph = SubGraph(pattern_dfg,
                            pattern_dfg.get_source_activities(),
                            pattern_dfg.get_sink_activities())

        subgraph.add_to_petri_net(petri_net)
        petri_net.prune()

        self.assertEqual(4, len(petri_net.transitions))
        self.assertEqual(5, len(petri_net.places))

if __name__ == '__main__':
    unittest.main()