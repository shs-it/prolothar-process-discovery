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
from prolothar_process_discovery.anomalydetection.traces.proseqo_supervised import ProseqoSupervised
from prolothar_process_discovery.anomalydetection.traces.proseqo_supervised import Proseqo

class TestProseqoSupervised(unittest.TestCase):

    def setUp(self):
        self.log = EventLog.create_from_simple_activity_log([
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','4','5','1','2','6'],
            ['0','1','2','4','5','1','2','6'],
            ['0','1','2','4','5','4','5','1','7','2','6'],
            ['0','7','8','6']
        ])
        self.normal_traces = EventLog()
        self.normal_traces.traces = self.log.traces[0:-1]
        self.anomalies = EventLog()
        self.anomalies.traces = self.log.traces[-1:]
        self.detector = ProseqoSupervised(proseqo=Proseqo(max_nr_of_workers=1))

    def test_supervised_train_predict(self):
        self.detector.train(self.normal_traces, self.anomalies)
        normal_traces, anomalies = self.detector.predict(self.log)
        self.assertIsNotNone(normal_traces)
        self.assertIsNotNone(anomalies)
        self.assertEqual(self.normal_traces, normal_traces)
        self.assertEqual(self.anomalies, anomalies)

if __name__ == '__main__':
    unittest.main()
