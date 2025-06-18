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

from prolothar_process_discovery.models.bpmn.bpmn_process import BpmnProcess
from prolothar_process_discovery.models.bpmn.gateway import Gateway
from prolothar_process_discovery.models.bpmn.xor_gateway import XorGateway
from prolothar_process_discovery.models.bpmn.task import Task
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import find_isolated_sequences_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_loops import find_isolated_loops_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_choices import find_one_step_choices_in_dfg
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.one_step_optionals import find_one_step_optionals_in_dfg

class _NoGatewayTripletException(Exception):
    pass

class _NotATaskException(Exception):
    pass

class BpmnToPatternDfgConverter():
    """converts a BPMN Process to a pattern-directly-follows-graph.
    """

    def convert(self, bpmn_process: BpmnProcess) -> PatternDfg:
        """converts a BPMN Process to a pattern-directly-follows-graph"""
        pattern_dfg_with_element_ids = PatternDfg.create_from_dfg(
                bpmn_process.get_dfg_with_element_ids())

        for start_end_event in itertools.chain(
                bpmn_process.get_start_events(), bpmn_process.get_end_events()):
            pattern_dfg_with_element_ids.remove_node(start_end_event.get_id())

        pattern_dfg_with_element_ids = self.__care_about_loops(
                pattern_dfg_with_element_ids, bpmn_process)

        pattern_dfg_with_element_ids = self.__replace_gateways(
                pattern_dfg_with_element_ids, bpmn_process)

        self.__remove_leftover_converging_gateways(
                pattern_dfg_with_element_ids, bpmn_process)

        pattern_dfg_with_element_ids = self.__fold_pattern_dfg(
                pattern_dfg_with_element_ids)

        pattern_dfg_with_element_ids = self.__replace_ids_with_names(
                pattern_dfg_with_element_ids, bpmn_process)

        pattern_dfg_with_element_ids.remove_degenerated_patterns()

        return pattern_dfg_with_element_ids

    def __care_about_loops(
                self, pattern_dfg_with_element_ids: PatternDfg,
                bpmn_process: BpmnProcess) -> PatternDfg:
        pattern_dfg = pattern_dfg_with_element_ids.copy()
        for loop in find_isolated_loops_in_dfg(pattern_dfg):
            start_activities = loop.start_activities()
            end_activities = loop.end_activities()
            if len(start_activities) == 1 and len(end_activities) == 1:
                start_element = bpmn_process.get_element_by_id(
                        next(iter(start_activities)))
                end_element = bpmn_process.get_element_by_id(
                        next(iter(end_activities)))
                if isinstance(start_element, Gateway) \
                and start_element.get_direction() == Gateway.Direction.CONVERGING \
                and isinstance(end_element, Gateway) \
                and end_element.get_direction() == Gateway.Direction.DIVERGING:
                    loop.fold_dfg(pattern_dfg)
        return pattern_dfg

    def __fold_pattern_dfg(self, pattern_dfg: PatternDfg) -> PatternDfg:
        change = True
        while change:
            change = False
            for pattern_finder in [
                    find_isolated_sequences_in_dfg,
                    find_isolated_loops_in_dfg,
                    find_one_step_choices_in_dfg,
                    find_one_step_optionals_in_dfg]:
                patterns = pattern_finder(pattern_dfg)
                if patterns:
                    pattern_dfg = pattern_dfg.fold(patterns)
                    change = True

        return pattern_dfg

    def __replace_gateways(
                self, pattern_dfg_with_element_ids: PatternDfg,
                bpmn_process: PatternDfg):
        diverging_gateway = self.__find_diverging_gateway(
                pattern_dfg_with_element_ids, bpmn_process)
        while diverging_gateway is not None:
            if isinstance(diverging_gateway, XorGateway):
                pattern_dfg_with_element_ids.remove_node(
                        diverging_gateway.get_id(), create_connections=True)
            else:
                pattern_dfg_with_element_ids = self.__fold_pattern_dfg_from_gateway(
                        diverging_gateway, pattern_dfg_with_element_ids,
                        bpmn_process)

            diverging_gateway = self.__find_diverging_gateway(
                pattern_dfg_with_element_ids, bpmn_process)
        return pattern_dfg_with_element_ids

    def __fold_pattern_dfg_from_gateway(
            self, diverging_gateway: Gateway,
            pattern_dfg_with_element_ids: PatternDfg,
            bpmn_process: BpmnProcess) -> PatternDfg:
        branch_starts = [
            element_id for element_id in
            pattern_dfg_with_element_ids.get_following_activities(
                    diverging_gateway.get_id())
        ]
        branches = [[] for branch in branch_starts]
        branches_to_remove = []
        for i,branch in enumerate(branches):
            next_ids = [branch_starts[i]]
            visited_ids = set()
            while next_ids:
                next_id = next_ids.pop()
                visited_ids.add(next_id)
                try:
                    next_element = bpmn_process.get_element_by_id(next_id)
                    if next_element.is_gateway():
                        #we want to build the patterns from the inside to the outside
                        if next_element.get_direction() == Gateway.Direction.DIVERGING:
                            return self.__fold_pattern_dfg_from_gateway(
                                    next_element, pattern_dfg_with_element_ids,
                                    bpmn_process)
                        elif next_element.get_direction() == Gateway.Direction.MIXED:
                            branches_to_remove.append(i)
                    else:
                        branch.append(next_element.get_id())
                        next_ids.extend(set(
                            pattern_dfg_with_element_ids.get_following_activities(
                                next_element.get_id())).difference(visited_ids))
                except KeyError:
                    #element has already been converted to a pattern
                    branch.append(next_id)
                    next_ids.extend(set(
                        pattern_dfg_with_element_ids.get_following_activities(
                            next_id)).difference(visited_ids))

        branches = [branch for i,branch in enumerate(branches)
                    if i not in branches_to_remove]
        if all(not branch for branch in branches):
            pattern_dfg_with_element_ids.remove_node(
                    diverging_gateway.get_id(), create_connections=True)
            return pattern_dfg_with_element_ids

        if any(not branch for branch in branches):
            pattern_dfg = pattern_dfg_with_element_ids.fold({
                Optional(diverging_gateway.create_pattern([
                    SubGraph(self.__fold_pattern_dfg(
                        pattern_dfg_with_element_ids.select_nodes(branch)),
                        [], [])
                    for branch in branches if branch
                ]))
            ])
        else:
            gateway_pattern = diverging_gateway.create_pattern([
                SubGraph(self.__fold_pattern_dfg(
                    pattern_dfg_with_element_ids.select_nodes(branch)), [], [])
                for branch in branches
            ])
            try:
                pattern_dfg = pattern_dfg_with_element_ids.fold({gateway_pattern])
            except KeyError as e:
                print(e)
        pattern_dfg.remove_node(diverging_gateway.get_id(),
                                create_connections=True)
        return pattern_dfg

    def __find_diverging_gateway(
                self, pattern_dfg_with_element_ids: PatternDfg,
                bpmn_process: BpmnProcess) -> Gateway:
        for element_id in pattern_dfg_with_element_ids.nodes.keys():
            try:
                element = bpmn_process.get_element_by_id(element_id)
                if isinstance(element, Gateway) \
                and element.get_direction() == Gateway.Direction.DIVERGING:
                    return element
            except KeyError:
                #element already has been transformed to a pattern and thus has
                #no longer an equivalent element in the BPMN graph
                pass
        return None

    def __replace_ids_with_names(
            self, pattern_dfg_with_element_ids: PatternDfg,
            bpmn_process: BpmnProcess) -> PatternDfg:
        for node in list(pattern_dfg_with_element_ids.get_nodes()):
            try:
                self.__replace_ids_with_names_in_pattern(
                        node.pattern, bpmn_process)
                if node.activity != node.pattern.get_activity_name():
                    pattern_dfg_with_element_ids.rename_activity(
                            node.activity, node.pattern.get_activity_name())
            except _NotATaskException:
                pattern_dfg_with_element_ids.remove_node(
                    node.activity, create_connections=True)

        pattern_dfg_with_element_ids.remove_degenerated_patterns()

        return pattern_dfg_with_element_ids

    def __replace_ids_with_names_in_pattern(
            self, pattern: Pattern, bpmn_process):
        if pattern.is_singleton():
            task = bpmn_process.get_element_by_id(pattern.activity)
            if not isinstance(task, Task):
                raise _NotATaskException()
            pattern.activity = task.get_name()
        else:
            activities_for_removal = []
            for subpattern in pattern.get_subpatterns():
                try:
                    self.__replace_ids_with_names_in_pattern(
                            subpattern, bpmn_process)
                except _NotATaskException:
                    activities_for_removal.append(subpattern.activity)
            if len(activities_for_removal) >= len(pattern.get_activity_set()):
                raise _NotATaskException()
            for activity in activities_for_removal:
                pattern.remove_activity(activity)
        pattern.clear_cache()


    def __remove_leftover_converging_gateways(
            self, pattern_dfg: PatternDfg, bpmn_process: BpmnProcess):
        for element_id in list(pattern_dfg.nodes.keys()):
            try:
                element = bpmn_process.get_element_by_id(element_id)
                if isinstance(element, Gateway) \
                and element.get_direction() == Gateway.Direction.CONVERGING:
                    pattern_dfg.remove_node(element_id, create_connections=True)
            except KeyError:
                #element already has been transformed to a pattern and thus has
                #no longer an equivalent element in the BPMN graph
                pass

