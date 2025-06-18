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
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from typing import List, Dict, Tuple, FrozenSet

class PatternStream:
    """pattern stream of cover, i.e. a stream of patterns that is used to
    cover (= encode) a set of sequences"""

    def __init__(self, store_patterns=False):
        """creates a new pattern stream.

        Args:
            possible_patterns:
                A list of patterns that can be present in the pattern stream.
                this is needed to initialize the prequential codes to uniform
                probability.
            store_patterns:
                default is False. If true, the patterns in the
                stream are explicitly stored in memory when "add" is called.
                This is useful, if one really needs to know the sequence of the
                added patterns
        """
        ...

    def copy_counts_only(self) -> PatternStream:
        """returns a copy of this stream. Only the counts are copied.
        All caches and any other information is not copied
        """
        ...

    def add(self, pattern: Pattern, usable_pattern_activities: frozenset,
            add_to_cache: bool = True, count: int = 1):
        """adds a pattern code to this stream
        Args:
            pattern:
                the pattern that is used for encoding the data and is added
                to this stream. must be in the list of possible patterns that
                has been given to the constructor. otherwise the computed
                code length will be wrong.
            usable_pattern_activities:
                gives the activity names of all patterns that could have been
                used at this stage - inclusive the pattern that has been used
            add_to_cache:
                has only internal usage and should not be used by other classes
        """
        ...

    def remove(self, pattern: Pattern, usable_pattern_activities: frozenset,
               count: int = 1):
        """removes counts from this pattern stream"""
        ...

    def remove_pattern_from_context(
            self, context: frozenset, pattern: Pattern):
        ...

    def get_code_length(self, verbose=False) -> float:
        """
        Returns:
            the encoded length of this pattern stream
        """
        ...

    def get_sequence_of_added_patterns(self) -> List[Pattern]:
        """returns a list with all patterns added to the stream. the order
        is the same as they have been added to stream. if a patterns has been
        added multiple times to the stream it will occur multiple times in this
        list.

        Raises:
            ValueError:
                if the pattern stream was not iniatialized with
                "store_patterns=True"
        """
        ...

    def get_usage_per_pattern(self) -> Dict[str, int]:
        """returns a dict with activity name => total usage"""
        ...

    def get_conditional_usage_per_pattern(
            self) -> Dict[FrozenSet[str], Dict[str, int]]:
        """
        returns a nested dictionary (alternative patterns) -> pattern -> count
        """
        ...

    def start_trace_covering(self, trace: Tuple[str]):
        """signal that now the given trace starts to get covered"""
        ...

    def end_trace_covering(self, trace: Tuple[str]):
        """signal that now the given trace is get covered"""
        ...

    def use_cache_to_cover_trace(self, trace: Tuple[str]):
        """repeats the addition of codes as it is stored in a cache for the
        same sequence of activities as the given trace"""
        ...
