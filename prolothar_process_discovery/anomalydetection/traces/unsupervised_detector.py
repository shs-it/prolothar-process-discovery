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

from abc import ABC, abstractmethod
from typing import Tuple

from prolothar_common.models.eventlog import EventLog

class UnsupervisedDetector(ABC):
    """
    template class for a unsupervised anomaly detecto
    """

    @abstractmethod
    def apply(self, log: EventLog) -> Tuple[EventLog, EventLog]:
        """
        splits the given EventLog into normal_traces and anomalies based on
        the predictions of this detector. this is a unsupervised prediction.

        Parameters
        ----------
        log : EventLog
            set of traces that will be split into normal data and anomalies

        Returns
        -------
        Tuple[EventLog, EventLog]
            normal_traces, anomalies
        """
        pass