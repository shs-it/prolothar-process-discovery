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
import itertools
from prolothar_common.models.eventlog import Trace, Event

class TraceToCharacterTranslator:
    """translates EventLog Traces into character strings. every activity
    in the EventLog gets its own unique character. This can be useful if
    one wants to apply Levenshtein Distance or other metrics on Traces
    """

    def __init__(self):
        #A - Z
        #a - z
        #0 - @
        #desparated try to have more one character symbols
        self.__iterator = iter(itertools.chain(range(65,91),
                        range(97,123),
                        range(48,65),
                        range(161,1000)))
        self.__character_table = {}

    def translate_trace(self, trace: Trace) -> str:
        return ''.join(self.__translate_event(event) for event in trace.events)

    def __translate_event(self, event: Event) -> str:
        if event.activity_name not in self.__character_table:
            self.__character_table[event.activity_name] = chr(next(self.__iterator))
        return self.__character_table[event.activity_name]
