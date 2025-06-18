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
from prolothar_common.models.dfg.node import Node
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_process_discovery.discovery.proseqo.pattern.loop import Loop
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.candidates import Candidate
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.pattern_candidate_generator import PatternCandidateGenerator

from typing import Iterable, List, Tuple

class OnePatternCandidateGenerator(PatternCandidateGenerator):
    """tries to express the process as one big pattern by conducting the
    following steps:
        1.
    """

    def _generate_patterns(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Candidate]:
        sequence = self.__create_sequence_from_pattern_dfg(pattern_dfg)

        if not sequence:
            return []

        eventually_follows_graph = \
            DirectlyFollowsGraph.build_eventually_follows_on_first_occurence_graph(log)

        i = 0
        while i < len(sequence):
            if isinstance(sequence[i], Choice):
                choice_without_wrong_ordered_options, wrong_ordered_options = \
                    self.__remove_wrong_ordered_options(
                        sequence[i], eventually_follows_graph)
                if wrong_ordered_options:
                    sequence[i] = choice_without_wrong_ordered_options
                    self.__insert_wrong_ordered_options(
                            sequence, i, wrong_ordered_options,
                            eventually_follows_graph)
            i += 1

        return [Sequence(sequence)]

    def __fold_self_loops(self, pattern_dfg: PatternDfg) -> PatternDfg:
        loops = []
        for node in pattern_dfg.get_nodes():
            if node.is_followed_by(node.activity):
                loops.append(Loop(node.pattern))
        return pattern_dfg.fold(loops)

    def __remove_ingoing_edges_of_ancestors(
            self, node: Node, pattern_dfg: PatternDfg):
        edges_to_remove = []
        for edge in node.edges:
            for edge_to_delete in edge.end.ingoing_edges:
                edges_to_remove.append((edge_to_delete.start.activity,
                                        edge_to_delete.end.activity))
        for edge_to_delete in edges_to_remove:
            pattern_dfg.remove_edge(edge_to_delete)

    def __create_sequence_from_pattern_dfg(
            self, pattern_dfg: PatternDfg) -> List[Pattern]:
        pattern_dfg = self.__fold_self_loops(pattern_dfg)

        sequence = []
        source_nodes = pattern_dfg.get_source_nodes()
        while source_nodes:
            if len(source_nodes) == 1:
                sequence.append(source_nodes[0].pattern)
            else:
                sequence.append(Choice([node.pattern for node in source_nodes]))
            for node in source_nodes:
                self.__remove_ingoing_edges_of_ancestors(node, pattern_dfg)
                pattern_dfg.remove_node(node.activity)
            source_nodes = pattern_dfg.get_source_nodes()

        if len(sequence) > 1:
            return sequence
        else:
            return None

    def __remove_wrong_ordered_options(
            self, choice: Choice,
            eventually_follows_graph: DirectlyFollowsGraph) -> Tuple[
            Pattern, List[Pattern]]:
        remaining_options = []
        wrong_ordered_options = []
        for option in choice.get_subpatterns():
            if self.__is_option_wrong_ordered(option, choice.get_subpatterns(),
                                              eventually_follows_graph):
                wrong_ordered_options.append(option)
            else:
                remaining_options.append(option)

        if not wrong_ordered_options:
            return choice, wrong_ordered_options
        elif len(remaining_options) == 1:
            return remaining_options[0], wrong_ordered_options
        elif len(remaining_options) > 1:
            return Choice(remaining_options), wrong_ordered_options
        else:
            return choice, None

    def __is_option_wrong_ordered(
            self, option: Pattern, all_options: Iterable[Pattern],
            eventually_follows_graph: DirectlyFollowsGraph) -> bool:
        """returns True iff there is option that clearly precedes the given
        option"""
        for other_option in all_options:
            if self.__clearly_precedes(other_option, option,
                                       eventually_follows_graph):
                return True
        return False

    def __clearly_precedes(
            self, potential_precedessor: Pattern, potential_ancestor: Pattern,
            eventually_follows_graph: DirectlyFollowsGraph) -> bool:
        for pre_activity in potential_precedessor.get_activity_set():
            for post_activity in potential_ancestor.get_activity_set():
                if (pre_activity,
                    post_activity) not in eventually_follows_graph.edges:
                    return False
        return True

    def __insert_wrong_ordered_options(
            self, sequence: List[Pattern], current_index: int,
            wrong_ordered_options: List[Pattern],
            eventually_follows_graph: DirectlyFollowsGraph):
       for option in wrong_ordered_options:
           self.__insert_wrong_ordered_option(sequence, current_index, option,
                                              eventually_follows_graph)

    def __insert_wrong_ordered_option(
            self, sequence: List[Pattern], current_index: int, option: Pattern,
            eventually_follows_graph: DirectlyFollowsGraph):
        i = current_index + 1
        if i < len(sequence):
            if self.__clearly_precedes(sequence[i], option,
                                       eventually_follows_graph):
                self.__insert_wrong_ordered_option(
                        sequence, i, option, eventually_follows_graph)
            else:
                sequence.insert(i, option)
        else:
            #end of sequence reached
            sequence.append(option)