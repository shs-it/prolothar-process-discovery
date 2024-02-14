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
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_common.models.data_petri_net import DataPetriNet

class TestChoice(unittest.TestCase):

    def test_add_to_petri_net(self):
        petri_net = DataPetriNet()

        choice = Choice([Singleton('A'), Singleton('B')])

        choice.add_to_petri_net(petri_net)
        petri_net.prune()

        self.assertEqual(4, len(petri_net.transitions))
        self.assertEqual(4, len(petri_net.places))

if __name__ == '__main__':
    unittest.main()