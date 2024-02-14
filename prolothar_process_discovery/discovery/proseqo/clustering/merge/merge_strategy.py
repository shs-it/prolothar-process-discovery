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

from prolothar_common.models.eventlog import EventLog

from typing import List

class MergeStrategy(ABC):
    @abstractmethod
    def merge(self, clusters: List[EventLog], verbose=False):
        pass

    @abstractmethod
    def clear_cache(self):
        """deletes all cached information if the implementation uses caching"""
