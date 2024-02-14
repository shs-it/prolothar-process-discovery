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

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.parallel import Parallel
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.cliques import find_cliques_of_size_2
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.cliques import merge_2_cliques

from typing import Set, Tuple, List, Dict

from collections import deque

def find_perfect_matching_parallels_in_dfg(dfg: DirectlyFollowsGraph) -> Set[Parallel]:
    """filters "find_parallel_candidates_in_dfg" for perfect matching parallels
    only, i.e. A||B||C is returned as pattern iff A,B,C is a full-clique and
    A,B,C have exactly the same set of predecessor and ancestors of non-clique
    members.
    """
    #candidate must be a full-clique
    candidates = []
    for candidate in find_parallel_candidates_in_dfg(dfg):
        if _parallel_is_full_clique(candidate, dfg):
            candidates.append(candidate)

    #all branches of candidate must have same predecessor and ancestor set
    perfect_matching_parallels = []
    for candidate in candidates:
        clique_member_set = set(branch.get_activity_name()
                                for branch in candidate.branches)
        preceding_activities = set(dfg.get_preceeding_activities(
                candidate.branches[0].get_activity_name())).difference(
                clique_member_set)
        following_activities = set(dfg.get_following_activities(
                candidate.branches[0].get_activity_name())).difference(
                clique_member_set)
        for branch in candidate.branches[1:]:
            branch_preceding_activities = set(dfg.get_preceeding_activities(
                        branch.get_activity_name())).difference(clique_member_set)
            branch_following_activities = set(dfg.get_following_activities(
                        branch.get_activity_name())).difference(clique_member_set)
            if (preceding_activities != branch_preceding_activities or
                following_activities != branch_following_activities):
                break
        else:
            perfect_matching_parallels.append(candidate)
    return perfect_matching_parallels

def _parallel_is_full_clique(
        parallel: Parallel, dfg: DirectlyFollowsGraph) -> bool:
    for i,branch in enumerate(parallel.branches):
        for j,other_branch in enumerate(parallel.branches):
            if i != j and not (
                    dfg.nodes[branch.get_activity_name()].is_followed_by(
                            other_branch.get_activity_name()) and
                    dfg.nodes[other_branch.get_activity_name()].is_followed_by(
                            branch.get_activity_name())):
                return False
    return True

def find_parallel_candidates_in_dfg(
        dfg: DirectlyFollowsGraph) -> Set[Parallel]:
    """returns a set of detected parallel patterns in the given
    DirectlyFollowsGraph. the detection is very dumb and should only be seen
    as a possibility that needs to be checked"""
    parallels = set()
    cliques = merge_2_cliques(find_cliques_of_size_2(dfg))
    for clique in cliques:
        parallels.add(Parallel([Singleton(a) for a in clique]))

    if isinstance(dfg, PatternDfg):
        for parallel in parallels:
            parallel.clear_cache()
            parallel.branches = [dfg.nodes[p.activity].pattern
                                 for p in parallel.branches]

    return parallels

def find_binary_parallel_candidates_in_dfg(
        dfg: DirectlyFollowsGraph) -> Set[Parallel]:
    """returns a set of detected parallel patterns with two branches in the given
    DirectlyFollowsGraph. the detection is very dumb and should only be seen
    as a possibility that needs to checked"""

    parallels = set([Parallel([Singleton(a) for a in clique])
                     for clique in find_cliques_of_size_2(dfg)])

    if isinstance(dfg, PatternDfg):
        for parallel in parallels:
            parallel.branches = [dfg.nodes[p.activity].pattern
                                 for p in parallel.branches]

    return parallels

def find_parallel_subgraphs(
        dfg: DirectlyFollowsGraph, log: EventLog) -> List[Parallel]:
    parallel_relations_dict = _create_parallel_relations_dict(dfg)

    list_of_none_parallel_sets = _create_list_of_none_parallel_sets(
            parallel_relations_dict)

    maximal_non_parallel_sets = _create_maximal_non_parallel_sets(
            list_of_none_parallel_sets)

    maximal_non_parallel_sets = _filter_maximal_sets(maximal_non_parallel_sets)

    return _transform_maximal_non_parallel_sets_into_parallels(
            parallel_relations_dict, maximal_non_parallel_sets, log)

def _filter_maximal_sets(maximal_non_parallel_sets):
    filtered_sets = []
    for maximal_set in maximal_non_parallel_sets:
        if len([ms for ms in maximal_non_parallel_sets
               if maximal_set != ms and maximal_set.intersection(ms)]) <= 1:
            filtered_sets.append(maximal_set)
    return filtered_sets


def _transform_maximal_non_parallel_sets_into_parallels(
            parallel_relations_dict: Dict[str, Set[str]],
            maximal_non_parallel_sets: List[Set[str]],
            log: EventLog) -> List[Parallel]:
    left_sets = deque(maximal_non_parallel_sets)
    new_left_sets = deque()
    branches = []
    parallels = []
    while left_sets:
        maximal_non_parallel_set = left_sets.pop()

        parallel_branches, non_parallel_branches = _check_parallelity(
               maximal_non_parallel_set, branches, parallel_relations_dict)

        if not non_parallel_branches:
            branches.append(set(maximal_non_parallel_set))
        elif len(non_parallel_branches) == 1:
            non_parallel_branches[0].update(maximal_non_parallel_set)
        elif not parallel_branches:
            new_left_sets.append(maximal_non_parallel_set)
            if not left_sets:
                parallels.append(_transform_branches_into_parallel(
                        branches, log))
                left_sets = new_left_sets
                branches = []

    if len(branches) > 1:
        parallels.append(_transform_branches_into_parallel(branches, log))
    return parallels

def _transform_branches_into_parallel(
        branches: List[Set[str]], log: EventLog) -> Parallel:
    parallel_subgraphs = []
    non_branches_activities = log.compute_activity_set().difference([
        activity for branch in branches for activity in branch
    ])

    for branch in branches:
        cut_log = log.copy()
        cut_log.filter_activities(branch)
        log_without_other_branches = log.copy()
        log_without_other_branches.filter_activities(non_branches_activities.union(branch))

        parallel_subgraphs.append(SubGraph(
                PatternDfg.create_from_event_log(
                        log_without_other_branches).select_nodes(branch),
                list(cut_log.compute_set_of_start_activities()),
                list(cut_log.compute_set_of_end_activities())))

    return Parallel(parallel_subgraphs)

def _check_parallelity(
        minimal_non_parallel_set: Set[str], branches: List[Set[str]],
        parallel_relations_dict: Dict[str, Set[str]]) -> Tuple[
            List[List[Set[str]]], List[List[Set[str]]]]:
   parallel_branches = []
   non_parallel_branches = []
   for branch in branches:
       parallel_counter = 0
       for branch_activity in branch:
           for activity in minimal_non_parallel_set:
               if branch_activity in parallel_relations_dict[activity]:
                   parallel_counter += 1
               else:
                   parallel_counter -= 1
       if parallel_counter > 0:
           parallel_branches.append(branch)
       else:
           non_parallel_branches.append(branch)
   return parallel_branches, non_parallel_branches

def _create_maximal_non_parallel_sets(
        list_of_none_parallel_sets: List[Set[str]]) -> List[Set[str]]:
    maximal_non_parallel_sets = []
    for non_parallel_set in list_of_none_parallel_sets:
        if _is_maximal_set(non_parallel_set, list_of_none_parallel_sets):
            maximal_non_parallel_sets.append(non_parallel_set)
    return maximal_non_parallel_sets

def _is_maximal_set(
        non_parallel_set: Set[str],
        list_of_non_parallel_sets: List[Set[str]]) -> List[Set[str]]:
    for other_set in list_of_non_parallel_sets:
        if non_parallel_set != other_set and non_parallel_set.issubset(other_set):
            return False
    return True

def _create_list_of_none_parallel_sets(
        parallel_relations_dict: Dict[str, Set[str]]) -> List[Set[str]]:
    list_of_non_parallel_sets = [non_parallel_set
            for non_parallel_set in parallel_relations_dict.values()
            if non_parallel_set]
    remaining_sets = set()
    for i,non_parallel_set in enumerate(list_of_non_parallel_sets[:-1]):
        for other_set in list_of_non_parallel_sets[i+1:]:
            remaining_sets.add(frozenset(
                    non_parallel_set.intersection(other_set)))
            remaining_sets.add(frozenset(
                    non_parallel_set.intersection(other_set)))
    return [s for s in remaining_sets if s]

def _create_parallel_relations_dict(
        dfg: DirectlyFollowsGraph) -> Dict[str, Set[str]]:
    parallel_dict = {a: set() for a in dfg.nodes.keys()}

    for node in dfg.nodes.keys():
        for ancestor in dfg.get_following_activities(node):
            if (node not in parallel_dict[ancestor] and
                _have_parallel_relationship(node, ancestor, dfg)):
                    parallel_dict[node].add(ancestor)
                    parallel_dict[ancestor].add(node)

    return parallel_dict

def _have_parallel_relationship(node: str, ancestor: str,
                                dfg: DirectlyFollowsGraph) -> bool:
    predecessors = dfg.get_preceeding_activities(node)
    if ancestor in predecessors:
        for predecessor in predecessors:
            if ancestor in dfg.get_following_activities(predecessor):
                return True
    return False

def find_parallel_subgraphs2(log: EventLog) -> List[Parallel]:
    follows_graph = DirectlyFollowsGraph.\
        build_eventually_follows_on_first_occurence_graph(log)

    cliques = find_cliques_of_size_2(follows_graph)
    activities_in_cliques = set(a for clique in cliques for a in clique)
    follows_graph_with_cliques_only = follows_graph.select_nodes(
            activities_in_cliques)
    parallels = []
    for component in follows_graph_with_cliques_only.get_weakly_connected_components():
        parallels.extend(_find_parallel_subgraphs_in_follows_graph_component(
                follows_graph.select_nodes(component), log))
    return parallels

def _find_parallel_subgraphs_in_follows_graph_component(
        component: DirectlyFollowsGraph, log: EventLog) -> List[Parallel]:
    parallels = []

    component_without_clique_edges = component.copy()
    for clique in find_cliques_of_size_2(component):
        component_without_clique_edges.remove_edge((clique[0], clique[1]))
        component_without_clique_edges.remove_edge((clique[1], clique[0]))

    branches = component_without_clique_edges.get_weakly_connected_components()
    if len(branches) > 1:
        parallels.append(_transform_branches_into_parallel(branches, log))

    return parallels

