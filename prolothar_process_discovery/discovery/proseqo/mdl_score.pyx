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

from prolothar_common.models.dfg.node cimport Node
from prolothar_common.models.eventlog.eventlog import EventLog

from prolothar_common cimport mdl_utils

from prolothar_process_discovery.discovery.proseqo.pattern.pattern cimport Pattern
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import NR_OF_PATTERN_TYPES_WITH_SINGLETON
from prolothar_process_discovery.discovery.proseqo.greedy_cover cimport compute_cover
from prolothar_process_discovery.discovery.proseqo.cover cimport Cover
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import Candidate

from libcpp.cmath cimport log2

cpdef float compute_mdl_score(object log, PatternDfg dfg, set activity_set=None, bint verbose=False):
    """computes the minimum description length of the log and a model (dfg).
    this is MDL(PatternDfg) + MDL(Log|PatternDfg) = MDL(PatternDfg) + MDL(Cover).
    this means a cover is computed for computing the MDL.
    """
    cdef Cover cover = compute_cover(log.traces, dfg, store_patterns_in_pattern_stream=False, activity_set=activity_set)
    return compute_mdl_score_given_cover(cover, log, dfg, verbose=verbose)

cpdef float compute_mdl_score_given_cover(Cover cover, object log, PatternDfg dfg, bint verbose = False):
    """give same output as compute_mdl_score but with a precomputed cover"""
    cdef float mdl_score = compute_encoded_length_of_pattern_dfg(
            dfg, cover.get_activity_set(), verbose=verbose)
    mdl_score += cover.get_encoded_length_of_cover(log, verbose=verbose)
    return mdl_score

cpdef float compute_encoded_length_of_pattern_dfg(PatternDfg pattern_dfg, frozenset activity_set, bint verbose=False):
    """computes the model cost (cost of the pattern_dfg)"""
    cdef set model_activity_set = pattern_dfg.compute_activity_set()
    #this only happens in rare cases when the model is known and contains
    #activities that are not present in the sample log
    if len(model_activity_set) > len(activity_set):
        activity_set = model_activity_set
    #number of activities
    cdef float encoded_length = mdl_utils.L_N(len(activity_set))

    #number of nodes => nr of activities is an upper bound, since we do not allow
    #activities to occur in multiple patterns
    encoded_length += log2(<float>len(activity_set))
    #encode the individual patterns
    for node in pattern_dfg.get_nodes():
        encoded_length += log2(<float>NR_OF_PATTERN_TYPES_WITH_SINGLETON)
        code_length_of_pattern, available_activities_for_encoding = \
           (<Pattern>(<Node>node).pattern).get_encoded_length_in_code_table(activity_set)
        encoded_length += code_length_of_pattern
    if encoded_length < 0:
        raise ValueError()
    cdef int max_nr_of_edges = pattern_dfg.get_nr_of_nodes() ** 2
    encoded_length += log2(<float>(max_nr_of_edges + 1))
    #which edges are present or 0
    encoded_length += mdl_utils.log2binom(max_nr_of_edges,
                                          pattern_dfg.get_nr_of_edges())
    if verbose:
        print('encoded length of pattern DFG: %.2f' % encoded_length)
    return encoded_length

cpdef float estimate_mdl_score(
        PatternDfg pattern_dfg_without_candidate,
        Cover cover_without_candidate, 
        object candidate, 
        object log,
        DirectlyFollowsGraph dfg, 
        bint verbose = False):
    """computes an estimate for the MDL of the PatternDfg that results from the
    application of the given candidate
    """
    cdef Cover cover = cover_without_candidate.copy_counts_only()
    cdef PatternDfg pattern_dfg = candidate.estimate_cover_change(
            cover, pattern_dfg_without_candidate.copy(), dfg)

    cdef float mdl_score = compute_encoded_length_of_pattern_dfg(
            pattern_dfg, cover.get_activity_set(), verbose=verbose)
    mdl_score += cover.get_encoded_length_of_cover(log, verbose=verbose)
    return mdl_score

cpdef float estimate_lower_bound_mdl_score(
        PatternDfg pattern_dfg_without_candidate,
        Cover cover_without_candidate, 
        object candidate, 
        object log,
        DirectlyFollowsGraph dfg, 
        bint verbose = False):
    """computes an estimate in form of a lower bound for the MDL of the
    PatternDfg that results from the application of the given candidate
    """
    cdef Cover cover = cover_without_candidate.copy_counts_only()

    cdef PatternDfg pattern_dfg = candidate.estimate_cover_change_for_lower_bound(
            cover, pattern_dfg_without_candidate.copy(), dfg)

    cdef float mdl_score = compute_encoded_length_of_pattern_dfg(
            pattern_dfg, cover.get_activity_set(), verbose=verbose)
    mdl_score += cover.get_encoded_length_of_cover(log, verbose=verbose)
    return mdl_score
