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
from prolothar_process_discovery.discovery.proseqo.pattern.blob import Blob
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.blobs import find_binary_blob_candidates_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.blobs import find_blob_candidates_in_dfg
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg

class TestBlobs(unittest.TestCase):

    def test_find_binary_blob_candidates_in_dfg(self):
        dfg = PatternDfg()

        #non-blob
        dfg.add_count('a', 'b')
        dfg.add_count('b', 'c')
        dfg.add_count('c', 'd')
        dfg.add_count('d', 'e')
        dfg.add_count('e', 'f')

        #blob
        dfg.add_count('l', 'h')
        dfg.add_count('l', 'k')
        dfg.add_count('h', 'k')
        dfg.add_count('h', 'l')
        dfg.add_count('h', 'g')
        dfg.add_count('k', 'g')
        dfg.add_count('k', 'l')
        dfg.add_count('k', 'h')
        dfg.add_count('g', 'l')
        dfg.add_count('g', 'h')

        #blob to non-blob
        dfg.add_count('k', 'e')
        dfg.add_count('l', 'e')
        dfg.add_count('h', 'e')

        #non-blob to blob
        dfg.add_count('c', 'k')
        dfg.add_count('c', 'g')
        dfg.add_count('c', 'h')

        found_blobs = find_binary_blob_candidates_in_dfg(dfg)

        expected_blobs = [
            Blob({'g', 'h'}),
            Blob({'h', 'l'}),
            Blob({'k', 'l'}),
            Blob({'k', 'h'}),
        ]

        self.assertCountEqual(expected_blobs, found_blobs)

    def test_find_blob_candidates_in_dfg(self):
        dfg = PatternDfg()

        #non-blob
        dfg.add_count('a', 'b')
        dfg.add_count('b', 'c')
        dfg.add_count('c', 'd')
        dfg.add_count('d', 'e')
        dfg.add_count('e', 'f')

        #blob
        dfg.add_count('l', 'h')
        dfg.add_count('l', 'k')
        dfg.add_count('h', 'k')
        dfg.add_count('h', 'l')
        dfg.add_count('h', 'g')
        dfg.add_count('k', 'g')
        dfg.add_count('k', 'l')
        dfg.add_count('k', 'h')
        dfg.add_count('g', 'l')
        dfg.add_count('g', 'h')

        #blob to non-blob
        dfg.add_count('k', 'e')
        dfg.add_count('l', 'e')
        dfg.add_count('h', 'e')

        #non-blob to blob
        dfg.add_count('c', 'k')
        dfg.add_count('c', 'g')
        dfg.add_count('c', 'h')

        found_blobs = find_blob_candidates_in_dfg(dfg)

        expected_blobs = [
            Blob({'g', 'h', 'l', 'k'}),
        ]

        self.assertCountEqual(expected_blobs, found_blobs)

if __name__ == '__main__':
    unittest.main()