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
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_common.models.eventlog import Trace, Event
from prolothar_process_discovery.discovery.proseqo.cover import Cover

class TestCoveringSubgraph(unittest.TestCase):

    def test_process_covering_step(self):
        subgraph_dfg = PatternDfg()
        subgraph_dfg.add_count('A', 'B')
        subgraph_dfg.add_count('A', 'C')
        subgraph_dfg.add_count('B', 'D')
        subgraph_dfg.add_count('C', 'D')
        subgraph = SubGraph(subgraph_dfg, ['A'], ['B'])

        pattern_dfg = PatternDfg()
        pattern_dfg.add_node(subgraph.get_activity_name())
        pattern_dfg.add_pattern(subgraph.get_activity_name(), subgraph)
        cover = Cover(pattern_dfg, set(['A', 'B', 'C', 'D']))
        cover.start_trace_covering(Trace('1', [Event('A'),
                                               Event('B'),
                                               Event('D')]))

        covering_subgraph = subgraph.for_covering(None, None)

        covering_subgraph.process_covering_step(cover, None, 'A')
        covering_subgraph.process_covering_step(cover, 'A', 'B')
        covering_subgraph.process_covering_step(cover, 'B', 'D')

        #1.0 is the code length to distinguish B from C in the choice
        self.assertAlmostEqual(1.0, cover.meta_stream.get_code_length(),
                               delta=0.0001)

if __name__ == '__main__':
    unittest.main()