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
from prolothar_common.models.data_petri_net import DataPetriNet, Marking
from prolothar_common.models.data_petri_net import Place, Transition
from prolothar_common.models.data_petri_net import AcceptAlwaysGuard, AllOfGuard
from prolothar_common.models.data_petri_net import EqualGuard, TrueGuard, FalseGuard
from prolothar_common.models.data_petri_net import SmallerGuard, SmallerOrEqualGuard
from prolothar_common.models.data_petri_net import GreaterGuard, GreaterOrEqualGuard
from prolothar_common.models.eventlog import Trace, Event
from prolothar_common.models.data_petri_net import FloatVariable, IntVariable, BoolVariable
from prolothar_common.models.data_petri_net import make_id_unique

from typing import List, Tuple, Dict

from pqdict import pqdict
from collections import Counter
from functools import reduce
from copy import deepcopy

import pulp

MoveOfAlignment = Tuple[Event,Event]
Alignment = List[MoveOfAlignment]

def marking_equation_heuristic(alignment: Alignment,
                               product_net: DataPetriNet,
                               final_marking: Marking,
                               transition_costs: Dict,
                               trace: Trace, marking_cache:Dict=None):
    """https://pdfs.semanticscholar.org/bc86/babd7202481392c68f94203f2b1dbb39e52f.pdf
    https://www7.in.tum.de/um/courses/petri/SS2015/PNSkript-summary.pdf
    """
    #use the alignment to replay the petri net and set the initial marking
    #to the state after replaying the alignment => we want to have a heuristic
    #how many transitions to fire to complete the alignment
    __replay_product_net(product_net, alignment)
    initial_marking = product_net.get_marking()
    if initial_marking == final_marking:
        return 0
    if marking_cache is not None:
        hashable_marking = frozenset(initial_marking.items())
        if hashable_marking in marking_cache:
            return float('inf')

    lp = pulp.LpProblem('MarkingEquationHeuristic', pulp.LpMinimize)
    transition_id_to_variable_name = {}
    for i, transition in enumerate(product_net.transitions.values()):
        transition_id_to_variable_name[transition.id] = 'x%d' % i
    x = pulp.LpVariable.dicts('x', [x for x in transition_id_to_variable_name.values()],
                              lowBound=0, upBound=None, cat=pulp.LpInteger)

    lp += (pulp.lpSum([transition_costs[transition.id] *
                       x[transition_id_to_variable_name[transition.id]] \
                      for transition in product_net.transitions.values()]),
           "transition cost")
    for i,place in enumerate(product_net.places.values()):
        lp += (
                pulp.lpSum([
                    __incidence_value(place, transition) *
                    x[transition_id_to_variable_name[transition.id]]
                    for transition in product_net.transitions.values()
                ]) == final_marking[place.id] - initial_marking[place.id],
                "Nxb row %d" % i
        )

    #lp.writeLP('test.lp')
    lp.solve()

    heuristic_value = pulp.value(lp.objective)

    if marking_cache is not None:
        marking_cache[hashable_marking] = heuristic_value

    return heuristic_value

def __incidence_value(place: Place, transition: Transition):
        value = 0
        if place in transition.start_places:
            value -= 1
        if place in transition.end_places:
            value += 1
        return value

def __replay_product_net(product_net, alignment):
    for move in alignment:
        if is_log_move(move):
            transition_filter = lambda t: t.id.startswith('event_net_' + move[0].activity_name)
        elif is_model_move(move):
            transition_filter = lambda t: t.id == move[1].transition_id
        else:
            transition_filter = lambda t: t.id.startswith('event_net_sync_') and move[0].activity_name in t.label
        fireable_transitions = list(filter(
                transition_filter,
                product_net.get_fireable_transitions(ignore_guards=True)))
        if len(fireable_transitions) != 1:
            raise Exception('unexpected exception. nr of fireable transition: %d' % len(fireable_transitions))
        product_net.force_transition(fireable_transitions[0].id)

def create_product_net(petri_net: DataPetriNet, trace: Trace):
    """https://pdfs.semanticscholar.org/bc86/babd7202481392c68f94203f2b1dbb39e52f.pdf
    page 12
    """
    if not petri_net.is_workflow_net():
        raise ValueError('petri_net is expected to be a workflow net')
    product_net = petri_net.copy()
    place_counter = 0
    transition_counter = 0
    transition_cost = {}


    #Model moves
    process_net_transitions_dict = {}
    for transition in product_net.transitions.values():
        transition_cost[transition.id] = 1 if transition.visible else 0
        if not transition.label in process_net_transitions_dict:
            process_net_transitions_dict[transition.label] = []
        if transition.visible:
            process_net_transitions_dict[transition.label].append(transition)

    #Event net
    start_place_of_event_net = product_net.add_place(Place.with_empty_label(
            'event_net_place_' + str(place_counter)))
    current_place = start_place_of_event_net
    event_net_transitions = []
    for event in trace.events:
        place_counter += 1
        transition_counter += 1
        new_place = product_net.add_place(Place.with_empty_label(
            'event_net_place_' + str(place_counter)))
        new_transition = product_net.add_transition(Transition(
            'event_net_' + event.activity_name + '_' + str(transition_counter),
            label=event.activity_name))
        transition_cost[new_transition.id] = 1
        event_net_transitions.append(new_transition)
        product_net.add_connection(current_place, new_transition, new_place)
        current_place = new_place

    #Synchronous moves
    for event_net_transition in event_net_transitions:
        if event_net_transition.label in process_net_transitions_dict:
            #we must create a synchronous transition for every equal activity
            #pair in the event net and the process net
            _create_synchronous_moves_in_product_net(
                    product_net, event_net_transition,
                    process_net_transitions_dict[event_net_transition.label],
                    transition_cost)

    #create markings
    all_zero_marking = {}
    for place_id in product_net.places.keys():
        all_zero_marking[place_id] = 0
    initial_marking = dict(all_zero_marking)
    final_marking = dict(all_zero_marking)
    start_places, end_places = product_net.get_source_sink_places()
    for place in start_places:
        initial_marking[place.id] = 1
    for place in end_places:
        final_marking[place.id] = 1

    product_net.set_marking(initial_marking)

    return product_net, initial_marking, final_marking, transition_cost

def _create_synchronous_moves_in_product_net(
                    product_net, event_net_transition,
                    process_net_transitions, transition_cost):
    for process_net_transition in process_net_transitions:
        sync_transition = product_net.add_transition(Transition(
            make_id_unique('event_net_sync_' + event_net_transition.id,
                           product_net.transitions),
            label=event_net_transition.label))
        transition_cost[sync_transition.id] = 0
        _connect_sync_transition_to_transition(product_net,
                                               sync_transition,
                                               event_net_transition)
        _connect_sync_transition_to_transition(product_net,
                                               sync_transition,
                                               process_net_transition)

def _connect_sync_transition_to_transition(product_net, sync_transition,
                                           transition):
    for start_place in transition.start_places:
        for end_place in transition.end_places:
            product_net.add_connection(start_place, sync_transition, end_place)

def balanced_conformance(data_petri_net: DataPetriNet,
                         initial_marking: Marking,
                         final_marking: Marking,
                         trace: Trace) -> Alignment:
    """uses the A* algorithm to compute an optimal alignment for a
    DataPetriNet.
    http://www.padsweb.rwth-aachen.de/wvdaalst/publications/p865.pdf

    Args:
        - dpn: A Data Petri Net
        - initial_marking
        - final_marking
        - trace
        - cost_function

    Returns:
        - a balanced alignment
    """
    alignment = []
    current_heuristic = 0
    queue = pqdict()
    heuristic_cache = {}

    product_net, initial_marking_product, final_marking_product, transition_costs = \
        create_product_net(data_petri_net, trace)

    #heuristic is admissible => only if it is 0
    #(< 0.01 for numerical instability), we have to check if we have found
    #the final solution
    while not (current_heuristic < 0.01 and
               alignment_explains_log_trace(alignment, trace) and
               alignment_accepted_by_model(alignment, data_petri_net,
                                            initial_marking, final_marking)):
        product_net.set_marking(initial_marking_product)
        current_heuristic = marking_equation_heuristic(
                        alignment, product_net,
                        final_marking_product, transition_costs, trace,
                        marking_cache=heuristic_cache)
        if current_heuristic != float('inf'):
            for control_flow_successor in control_flow_successors(
                    data_petri_net, initial_marking, final_marking,
                    trace, alignment):
                _process_control_flow_successor(
                        control_flow_successor, data_petri_net,
                        current_heuristic, queue)

        if not queue:
            data_petri_net.set_marking(initial_marking)
            data_petri_net.plot()
            for move in alignment:
                if not is_log_move(move):
                    data_petri_net.force_transition(move[1].transition_id)
                    data_petri_net.plot()

        top_item = queue.popitem()[0]
        alignment = list(top_item[0])
        current_heuristic = top_item[1]

    return alignment

def _process_control_flow_successor(
        control_flow_successor: Alignment, data_petri_net: DataPetriNet,
        current_heuristic: float, queue: pqdict):
    augmented_control_flow_successor = augment_with_write_operations(
                        control_flow_successor, data_petri_net)
    if augmented_control_flow_successor is not None:
        cost = cost_function(augmented_control_flow_successor,
                             data_petri_net)
        queue.additem((tuple(augmented_control_flow_successor),
                       current_heuristic - 1),
                      cost + max(0, current_heuristic - 1))

def cost_function(alignment: Alignment, data_petri_net: DataPetriNet):
    cost = 0
    for move in alignment:
        cost_of_move = 0
        if is_log_move(move):
            cost_of_move = 1
        #model moves only cost something if the transition is visible
        elif (is_model_move(move) and
              data_petri_net.transitions[move[1].transition_id].visible):
            cost_of_move = 1 + len(move[1].attributes)
        else:
            for attribute_name in move[0].attributes.keys():
                if (move[0].attributes[attribute_name] !=
                    move[1].attributes[attribute_name]):
                    cost_of_move += 1
        cost += cost_of_move
    return cost

def alignment_explains_log_trace(alignment: Alignment, trace: Trace) -> bool:
    trace_index = 0
    for move in alignment:
        if not is_model_move(move):
            trace_index += 1
    return trace_index == len(trace.events)

def alignment_accepted_by_model(alignment: Alignment,
                                data_petri_net: DataPetriNet,
                                initial_marking: Marking,
                                final_marking: Marking) -> bool:
    data_petri_net.set_marking(initial_marking)
    for move in alignment:
        if not is_log_move(move):
            data_petri_net.force_transition(move[1].transition_id)
    return data_petri_net.matches_marking(final_marking)

def control_flow_successors(data_petri_net: DataPetriNet,
                            initial_marking: Marking,
                            final_marking: Marking,
                            trace: Trace,
                            alignment: Alignment):

    #step 1: synchronize net with alignment and find out, which is the next
    #event of trace, which needs to get covered
    data_petri_net.set_marking(initial_marking)
    trace_index = 0
    for move in alignment:
        if not is_log_move(move):
            data_petri_net.force_transition(move[1].transition_id)
        if not is_model_move(move):
            trace_index += 1
    next_event_to_cover = None if trace_index >= len(trace.events) else trace.events[trace_index]

    #step 2: extend existing alignment with possible moves:
    # 2.1 model move
    # 2.2 log move
    # 2.3 synchronous move if possible

    possible_model_transitions = data_petri_net.get_fireable_transitions(
                    ignore_guards=True)

    if (_are_all_transitions_hidden(possible_model_transitions) and
        _are_all_transitions_conflict_free(possible_model_transitions)):
        return _create_control_flow_successors_for_hidden_only_transitions(
                alignment, possible_model_transitions, next_event_to_cover)
    else:
        return _create_control_flow_successors_for_transitions(
                alignment, possible_model_transitions, next_event_to_cover)

def _are_all_transitions_hidden(transitions: List[Transition]) -> bool:
    for transition in transitions:
        if transition.visible:
            return False
    return True

def _are_all_transitions_conflict_free(transitions: List[Transition]) -> bool:
    place_id_set = set()
    for transition in transitions:
        for place in transition.start_places:
            if place.id in place_id_set:
                return False
            place_id_set.add(place.id)
    return True

def _create_control_flow_successors_for_hidden_only_transitions(
        alignment: Alignment,
        possible_model_transitions: List[Transition],
        next_event_to_cover: Event) -> List[Alignment]:
    control_flow_successor = alignment + []

    for t in possible_model_transitions:
        control_flow_successor.append(
                (Event(None), Event(t.label, transition_id=t.id)))

    return [control_flow_successor]

def _create_control_flow_successors_for_transitions(
        alignment: Alignment,
        possible_model_transitions: List[Transition],
        next_event_to_cover: Event) -> List[Alignment]:
    control_flow_successors_list = []

    for t in possible_model_transitions:
        # 2.1 model move
        control_flow_successors_list.append(alignment + [
                (Event(None), Event(t.label, transition_id=t.id))])


        # 2.3 synchronous move if possible
        if (next_event_to_cover is not None and
            t.label == next_event_to_cover.activity_name):
            control_flow_successors_list.append(
                    alignment + [(next_event_to_cover,
                                  Event(t.label, transition_id=t.id))])

    # 2.2 log move
    if next_event_to_cover is not None:
        control_flow_successors_list.append(alignment + [(next_event_to_cover,
                                                     Event(None))])

    return control_flow_successors_list

def augment_with_write_operations(alignment: Alignment,
                                  data_petri_net: DataPetriNet,
                                  M=2**31-1):
    """
    http://bpmcenter.org/wp-content/uploads/reports/2013/BPM-13-05.pdf
    """
    #we only need to augment, if the log moves contain attributes
    if _contains_attributes(alignment):
        if data_petri_net.has_guards():
            alignment = _augment_with_write_operations_lp(data_petri_net,
                                                          alignment, M=M)
        else:
            alignment = _augment_with_write_operations_simple(alignment)

    return alignment

def _augment_with_write_operations_simple(alignment: Alignment):
    """if there are not guards in the model, then we can easily augment the
    write operations by copying the variables in the log alignment part
    """
    for move in alignment:
        move[1].attributes = dict(move[0].attributes)
    return alignment

def _augment_with_write_operations_lp(data_petri_net, alignment, M=2**31-1):
    lp = _solve_augment_lp_problem(data_petri_net, alignment, M=M)

    if pulp.LpStatus[lp.status] == 'Optimal':
        alignment = deepcopy(alignment)
        _map_lp_variables_on_alignment(lp.variables(), alignment,
                                       data_petri_net.variables)
    else:
        alignment = None

    return alignment

def _contains_attributes(alignment: Alignment):
    for move in alignment:
        if len(move[0].attributes) > 0:
            return True
    return False

def _map_lp_variables_on_alignment(lp_variables, alignment: Alignment,
                                   variables_in_model):
    lp_variables_dict = {variable.name: variable for variable in lp_variables}
    variable_name_counter = Counter()

    for move in alignment:
        for attribute_name in move[0].attributes.keys():
            variable_name_counter[attribute_name] += 1
            variable_name = '%s%r' % (attribute_name, variable_name_counter[attribute_name])
            numeric_value_of_variable = lp_variables_dict[variable_name].varValue
            if isinstance(variables_in_model[attribute_name], FloatVariable):
                mapped_value_of_variable = numeric_value_of_variable
            elif isinstance(variables_in_model[attribute_name], IntVariable):
                mapped_value_of_variable = int(numeric_value_of_variable)
            elif isinstance(variables_in_model[attribute_name], BoolVariable):
                mapped_value_of_variable = numeric_value_of_variable == 1.0
            else:
                raise ValueError('Unmapped variable type: %r' % variables_in_model[attribute_name].__class__)

            move[1].attributes[attribute_name] = mapped_value_of_variable

def _solve_augment_lp_problem(data_petri_net, alignment, M=2**31-1):
    lp = pulp.LpProblem('AugmentWithWriteOperations', pulp.LpMinimize)

    variables = []
    variables_hat = []
    variable_name_counter = Counter()
    constraints = []
    for move in alignment:
        variables_for_this_move, variables_hat_for_this_move, constraints_for_this_move = \
            _create_variables_and_constraints_for_move(
                    move, variable_name_counter, data_petri_net, M=M)
        variables.extend(variables_for_this_move.values())
        variables_hat.extend(variables_hat_for_this_move.values())
        constraints.extend(constraints_for_this_move)

    #min v1^ + v2^ + v3^ + ...
    if variables_hat:
        lp += (reduce(lambda a,b:a+b, variables_hat), 'Nr of deviating variable values')

    for constraint, comment in constraints:
        lp += (constraint, comment)

    lp.solve()
    return lp

def _create_hat_constraints(variables_for_this_move,
                            variables_hat_for_this_move):
    constraints = []
    for variable_name, variable in variables_for_this_move.items():
        constraints.append(())
    return constraints

def _create_variables_and_constraints_for_move(
        move, variable_name_counter, data_petri_net, M = 2**31-1):
    variables_for_move = {}
    variables_hat_for_move = {}
    constraints_for_move = []
    for attribute_name, attribute_value in move[0].attributes.items():
        variable_name_counter[attribute_name] += 1
        variable_name = '%s%r' % (attribute_name, variable_name_counter[attribute_name])
        _create_variable_that_stores_variable_value_in_alignment(
                variables_for_move, variable_name, data_petri_net.variables,
                attribute_name)
        _create_hat_variable(variables_hat_for_move, variable_name,
                             data_petri_net.variables, attribute_name)
        #create a constraint that v_hat = 0 <=> v = logvalue
        #according to the paper, this constraint is expressed by two <= constraints
        constraints_for_move.append((
            variables_for_move[attribute_name] - M * variables_hat_for_move[attribute_name] <= attribute_value,
            '%s - M * %s_hat <= logvalue (<= %r)' % (variable_name, variable_name, attribute_value)
        ))
        constraints_for_move.append((
            -variables_for_move[attribute_name] - M * variables_hat_for_move[attribute_name] <= -attribute_value,
            '-%s - M * %s_hat <= -logvalue (<= -%r)' % (variable_name, variable_name, attribute_value)
        ))
    #if there is a guard, we need to add a constraint for this guard
    #if this is a log move, there is no transition for this move in the model
    if not is_log_move(move):
        constraints_for_move.extend(_create_guard_constraints_for_move(
                variables_for_move,
                data_petri_net.transitions[move[1].transition_id].guard_function,
                variable_name_counter, data_petri_net))
    return variables_for_move, variables_hat_for_move, constraints_for_move

def _create_variable_that_stores_variable_value_in_alignment(
        variables_for_move, variable_name, attributes, attribute_name):
    variables_for_move[attribute_name] = pulp.LpVariable(
        variable_name,
        lowBound=attributes[attribute_name].get_lower_bound_as_number(),
        upBound=attributes[attribute_name].get_upper_bound_as_number(),
        cat=pulp.LpContinuous if isinstance(attributes[attribute_name], FloatVariable) else pulp.LpInteger
    )

def _create_hat_variable(variables_hat_for_move, variable_name,
                         attributes, attribute_name):
    """create binary (0,1) variable that expresses whether the alignment
       variable value matches the log variable value
    """
    variables_hat_for_move[attribute_name] = pulp.LpVariable(
        '%s_hat' % variable_name,
        lowBound=0,
        upBound=1,
        cat=pulp.LpContinuous if isinstance(attributes[attribute_name], FloatVariable) else pulp.LpInteger
    )
def _create_guard_constraints_for_move(variables_for_move, guard_function,
                                       variable_name_counter, data_petri_net):
    def constrain_comment():
        return '%s: %r' %(variables_for_move[guard_function.variable.name].name,
                          guard_function.__class__)
    guard_constraints = []

    if guard_function is None or isinstance(guard_function, AcceptAlwaysGuard):
        return guard_constraints

    #if the move is a log move and there is a guard in the model component of
    #the move, then the variables in the guard have not been added to the
    #variables dictionary yet.
    if (hasattr(guard_function, 'variable') and
        guard_function.variable.name not in variables_for_move):
        variable_name_counter[guard_function.variable.name] += 1
        variable_name = '%s%r' % (guard_function.variable.name,
                                  variable_name_counter[guard_function.variable.name])
        _create_variable_that_stores_variable_value_in_alignment(
                variables_for_move, variable_name,
                data_petri_net.variables,
                guard_function.variable.name)

    if isinstance(guard_function, AllOfGuard):
        for sub_guard in guard_function.guard_list:
            guard_constraints.extend(_create_guard_constraints_for_move(
                    variables_for_move, sub_guard, variable_name_counter,
                    data_petri_net))
    elif isinstance(guard_function, EqualGuard):
        guard_constraints.append((
                variables_for_move[guard_function.variable.name] == guard_function.compareValue,
                constrain_comment()))
    elif isinstance(guard_function, SmallerGuard):
        guard_constraints.append((
                variables_for_move[guard_function.variable.name] < guard_function.compareValue,
                constrain_comment()))
    elif isinstance(guard_function, SmallerOrEqualGuard):
        guard_constraints.append((
                variables_for_move[guard_function.variable.name] <= guard_function.compareValue,
                constrain_comment()))
    elif isinstance(guard_function, GreaterGuard):
        guard_constraints.append((
                variables_for_move[guard_function.variable.name] > guard_function.compareValue,
                constrain_comment()))
    elif isinstance(guard_function, GreaterOrEqualGuard):
        guard_constraints.append((
                variables_for_move[guard_function.variable.name] >= guard_function.compareValue,
                constrain_comment()))
    elif isinstance(guard_function, TrueGuard):
        guard_constraints.append((
                variables_for_move[guard_function.variable.name] == 1,
                constrain_comment()))
    elif isinstance(guard_function, FalseGuard):
        guard_constraints.append((
                variables_for_move[guard_function.variable.name] == 0,
                constrain_comment()))
    else:
        raise ValueError('No mapping for guard %r' % guard_function)

    return guard_constraints

def is_model_move(move: MoveOfAlignment) -> bool:
    """returns True iff this is a model move, i.e. a transition in the model
    with no equivalent (i.e. ">>") event in the log.
    This means move[0].activity_name is None.
    """
    return move[0].activity_name is None

def is_log_move(move: MoveOfAlignment) -> bool:
    """returns True iff this is a log move, i.e. an event in the log
    with no equivalent (i.e. ">>") transition in the model.
    This means move[1].activity_name is None.
    """
    return move[1].activity_name is None
