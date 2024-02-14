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
from prolothar_process_discovery.discovery.proseqo.clustering.similarity.string_similarity import StringSimilarity

from difflib import SequenceMatcher

class SequenceMatcherSimilarity(StringSimilarity):

    def is_symmetric(self) -> bool:
        return True

    def _compute_string_similarity(self, s1: str, s2: str) -> float:
         return SequenceMatcher(None, s1, s2).ratio()

    def __repr__(self) -> str:
        return 'SequenceMatcherSimilarity'