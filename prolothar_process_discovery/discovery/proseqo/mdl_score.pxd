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

from prolothar_common.models.directly_follows_graph cimport DirectlyFollowsGraph
from prolothar_process_discovery.discovery.proseqo.pattern_dfg cimport PatternDfg
from prolothar_process_discovery.discovery.proseqo.cover cimport Cover

cpdef float compute_mdl_score(object log, PatternDfg dfg, set activity_set=?, bint verbose=?)

cpdef float compute_mdl_score_given_cover(Cover cover, object log, PatternDfg dfg, bint verbose = ?)

cpdef float compute_encoded_length_of_pattern_dfg(PatternDfg pattern_dfg, frozenset activity_set, bint verbose=?)

cpdef float estimate_mdl_score(
        PatternDfg pattern_dfg_without_candidate,
        Cover cover_without_candidate, 
        object candidate, 
        object log,
        DirectlyFollowsGraph dfg, 
        bint verbose = ?)

cpdef float estimate_lower_bound_mdl_score(
        PatternDfg pattern_dfg_without_candidate,
        Cover cover_without_candidate, 
        object candidate, 
        object log,
        DirectlyFollowsGraph dfg, 
        bint verbose = ?)
