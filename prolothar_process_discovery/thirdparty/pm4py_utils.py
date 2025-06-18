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

from pm4py.objects.process_tree.obj import ProcessTree as Pm4PyProcessTree
from pm4py.objects.process_tree.obj import Operator as ProcessTreeOperator

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.pattern import Pattern
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_process_discovery.discovery.proseqo.pattern.parallel import Parallel
from prolothar_process_discovery.discovery.proseqo.pattern.loop import Loop
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional

def convert_pm4py_process_tree_to_pdfg(process_tree: Pm4PyProcessTree) -> PatternDfg:
    """converts a process tree from pm4py to a pattern directly follows graph.
    the graph will consist of one node with a pattern expressing the given
    process tree"""
    pattern_dfg = PatternDfg()
    pattern = create_pattern_from_process_tree(process_tree)
    pattern_dfg.add_node(pattern.get_activity_name())
    pattern_dfg.add_pattern(pattern.get_activity_name(), pattern)
    pattern_dfg.remove_degenerated_patterns()
    return pattern_dfg

def create_pattern_from_process_tree(process_tree: Pm4PyProcessTree) -> Pattern:
    pattern = None
    """converts a process tree from pm4py to a pattern"""
    if process_tree.operator == ProcessTreeOperator.SEQUENCE:
        pattern =  Sequence([create_pattern_from_process_tree(c)
                             for c in process_tree.children])
    elif process_tree.operator == ProcessTreeOperator.XOR:
        pattern = _create_choice_pattern_from_process_tree(process_tree)
    elif process_tree.operator == ProcessTreeOperator.PARALLEL:
        pattern = Parallel([create_pattern_from_process_tree(c)
                            for c in process_tree.children])
    elif process_tree.operator == ProcessTreeOperator.LOOP:
        pattern = _create_loop_pattern_from_process_tree(process_tree)
    elif process_tree.operator is None:
        pattern = Singleton(process_tree.label)
    else:
        raise NotImplementedError(process_tree.operator)
    return pattern

def _create_loop_pattern_from_process_tree(
        process_tree: Pm4PyProcessTree) -> Loop:
    visible_children = [child for child in process_tree.children
                        if child.operator is not None or child.label is not None]
    if len(process_tree.children) != 2:
        if len(visible_children) > 2 and not (
                len(visible_children) == 3 and
                visible_children[1].label == visible_children[2].label):
            raise NotImplementedError(process_tree)
    if (len(visible_children) == 1):
        pattern = Loop(create_pattern_from_process_tree(visible_children[0]))
    else:
        #this not completely equivalent but a good approximation if the pdfg
        #is only allowed to contain activities exactly once
        pattern = Loop(Sequence([
                create_pattern_from_process_tree(process_tree.children[0]),
                Optional(create_pattern_from_process_tree(process_tree.children[1]))]))
    return pattern

def _create_choice_pattern_from_process_tree(
        process_tree: Pm4PyProcessTree) -> Pattern:
    if [child for child in process_tree.children
        if child.operator is None and child.label is None]:
        pattern = Optional(Choice([create_pattern_from_process_tree(c)
                                   for c in process_tree.children
                                   if c.operator is not None or
                                   c.label is not None]))
    else:
        pattern = Choice([create_pattern_from_process_tree(c)
                          for c in process_tree.children])
    return pattern


