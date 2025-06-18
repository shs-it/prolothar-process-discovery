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

from prolothar_common.models.eventlog import EventLog
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.cover import Cover
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import Candidate

from typing import Set, Union

def compute_mdl_score(log: EventLog, dfg: PatternDfg,
                      activity_set: Union[Set[str],None]=None, verbose=False) -> float:
    """computes the minimum description length of the log and a model (dfg).
    this is MDL(PatternDfg) + MDL(Log|PatternDfg) = MDL(PatternDfg) + MDL(Cover).
    this means a cover is computed for computing the MDL.
    """
    ...

def compute_mdl_score_given_cover(cover, log: EventLog, dfg: PatternDfg,
                                  verbose: bool = False) -> float:
    """give same output as compute_mdl_score but with a precomputed cover"""
    ...

def compute_encoded_length_of_pattern_dfg(
        pattern_dfg: PatternDfg, activity_set: Set[str], verbose=False) -> float:
    """computes the model cost (cost of the pattern_dfg)"""
    ...


def estimate_mdl_score(
        pattern_dfg_without_candidate: PatternDfg,
        cover_without_candidate: Cover, candidate: Candidate, log: EventLog,
        dfg: DirectlyFollowsGraph, verbose: bool = False) -> float:
    """computes an estimate for the MDL of the PatternDfg that results from the
    application of the given candidate
    """
    ...

def estimate_lower_bound_mdl_score(
        pattern_dfg_without_candidate: PatternDfg,
        cover_without_candidate: Cover, candidate: Candidate, log: EventLog,
        dfg: DirectlyFollowsGraph, verbose: bool = False) -> float:
    """computes an estimate in form of a lower bound for the MDL of the
    PatternDfg that results from the application of the given candidate
    """
    ...
