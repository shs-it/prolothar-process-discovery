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

from pm4py.objects.process_tree.process_tree import ProcessTree
from pm4py.objects.process_tree.pt_operator import Operator as ProcessTreeOperator

from prolothar_process_discovery.thirdparty.pm4py_utils import convert_pm4py_process_tree_to_pdfg
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence

class TestPm4pyUtils(unittest.TestCase):

    def test_convert_pm4py_process_tree_to_pdfg(self):
        node_1 = ProcessTree(label='A')
        node_2 = ProcessTree(label='B')
        process_tree = ProcessTree(operator=ProcessTreeOperator.SEQUENCE,
                                   children=[node_1, node_2])
        pdfg = convert_pm4py_process_tree_to_pdfg(process_tree)
        self.assertIsNotNone(pdfg)
        self.assertEqual(1, pdfg.get_nr_of_nodes())
        pattern = Sequence.from_activity_list(['A', 'B'])
        self.assertEqual(pattern, list(pdfg.get_nodes())[0].pattern)

if __name__ == '__main__':
    unittest.main()