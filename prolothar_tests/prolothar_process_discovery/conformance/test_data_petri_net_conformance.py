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

import unittest
from prolothar_common.models.data_petri_net import DataPetriNet
from prolothar_common.models.data_petri_net import Place
from prolothar_common.models.data_petri_net import Transition
from prolothar_common.models.data_petri_net import IntVariable, BoolVariable
from prolothar_common.models.data_petri_net import Guard, SmallerOrEqualGuard, GreaterOrEqualGuard, FalseGuard
from prolothar_common.models.eventlog import Trace, Event
from prolothar_process_discovery.conformance.data_petri_net_conformance import control_flow_successors
from prolothar_process_discovery.conformance.data_petri_net_conformance import augment_with_write_operations
from prolothar_process_discovery.conformance.data_petri_net_conformance import balanced_conformance
from prolothar_process_discovery.conformance.data_petri_net_conformance import alignment_explains_log_trace
from prolothar_process_discovery.conformance.data_petri_net_conformance import create_product_net
from prolothar_process_discovery.conformance.data_petri_net_conformance import cost_function

class TestDataPetriNetConformance(unittest.TestCase):

    def setUp(self):
        self.net = DataPetriNet()

        start_place = self.net.add_place(
                Place.with_id_label('start', nr_of_tokens=1))
        choice_place = self.net.add_place(Place.with_empty_label('choice'))
        repeat_place = self.net.add_place(Place.with_empty_label('repeat'))
        end_place = self.net.add_place(Place.with_id_label('end'))

        start_computer = self.net.add_transition(Transition('start computer'))
        drink_coffee = self.net.add_transition(Transition('drink coffee'))
        program = self.net.add_transition(Transition('program'))
        visit_meeting = self.net.add_transition(Transition('visit meeting'))
        eat_lunch = self.net.add_transition(Transition('eat lunch'))
        shutdown_computer = self.net.add_transition(Transition('shutdown computer'))
        repeat = self.net.add_transition(Transition('repeat', visible=False))

        time = self.net.add_variable(IntVariable('time', lower_bound=0, upper_bound=24))
        tired = self.net.add_variable(BoolVariable('tired'))

        start_computer.set_guard_function(
            SmallerOrEqualGuard(time, 9))
        eat_lunch.set_guard_function(Guard.all_of([
            GreaterOrEqualGuard(time,12),
            SmallerOrEqualGuard(time, 13)
        ]))
        program.set_guard_function(FalseGuard(tired))
        shutdown_computer.set_guard_function(
            GreaterOrEqualGuard(time, 16))

        self.net.add_connection(start_place, start_computer, choice_place)
        self.net.add_connection(choice_place, drink_coffee, repeat_place)
        self.net.add_connection(choice_place, program, repeat_place)
        self.net.add_connection(choice_place, visit_meeting, repeat_place)
        self.net.add_connection(choice_place, eat_lunch, repeat_place)
        self.net.add_connection(repeat_place, repeat, choice_place)
        self.net.add_connection(repeat_place, shutdown_computer, end_place)

        self.initial_marking = {
            'start': 1, 'choice': 0, 'repeat': 0, 'end': 0
        }
        self.final_marking = {
            'start': 0, 'choice': 0, 'repeat': 0, 'end': 1
        }
        self.net.set_marking(self.initial_marking)

    def test_control_flow_successors_empty_alignment(self):
        trace = Trace(0, [
            Event('start computer', attributes = {'time': 9, 'tired': False}),
            Event('program', attributes = {'time': 10, 'tired': False}),
            Event('visit meeting', attributes = {'time': 11, 'tired': True}),
            Event('drink coffee', attributes = {'time': 12, 'tired': True}),
            Event('eat lunch', attributes = {'time': 12, 'tired': False}),
            Event('program', attributes = {'time': 13, 'tired': False}),
            Event('program', attributes = {'time': 15, 'tired': False}),
            Event('test', attributes = {'time': 16, 'tired': False}),
            Event('shutdown computer', attributes = {'time': 17, 'tired': True})
        ])

        self.maxDiff = None
        self.assertCountEqual(
            [
                [(trace.events[0], Event('start computer', transition_id='start computer'))],
                [(trace.events[0], Event(None))],
                [(Event(None), Event('start computer', transition_id='start computer'))]
            ],
            control_flow_successors(self.net, self.initial_marking,
                                    self.final_marking, trace, []))

    def test_control_flow_successors_alignment_with_two_moves(self):
        trace = Trace(0, [
            Event('start computer', attributes = {'time': 9, 'tired': False}),
            Event('program', attributes = {'time': 10, 'tired': False}),
            Event('visit meeting', attributes = {'time': 11, 'tired': True}),
            Event('drink coffee', attributes = {'time': 12, 'tired': True}),
            Event('eat lunch', attributes = {'time': 12, 'tired': False}),
            Event('program', attributes = {'time': 13, 'tired': False}),
            Event('program', attributes = {'time': 15, 'tired': False}),
            Event('test', attributes = {'time': 16, 'tired': False}),
            Event('shutdown computer', attributes = {'time': 17, 'tired': True})
        ])

        alignment = [
                (trace.events[0], Event('start computer', transition_id='start computer')),
                (trace.events[1], Event('program', transition_id='program'))
        ]
        self.maxDiff = None
        self.assertCountEqual(
            [
                alignment + [(Event(None), Event('shutdown computer', transition_id='shutdown computer'))],
                alignment + [(Event(None), Event('repeat', transition_id='repeat'))],
                alignment + [(trace.events[2], Event(None))]
            ],
            control_flow_successors(self.net, self.initial_marking,
                                    self.final_marking, trace, alignment))

    def test_augment_with_write_operations_feasible_solution(self):
        trace = Trace(0, [
            Event('start computer', attributes = {'time': 9, 'tired': False}),
            Event('program', attributes = {'time': 10, 'tired': False}),
            Event('visit meeting', attributes = {'time': 11, 'tired': True}),
            Event('drink coffee', attributes = {'time': 12, 'tired': True}),
            Event('eat lunch', attributes = {'time': 12, 'tired': False}),
            Event('program', attributes = {'time': 13, 'tired': False}),
            Event('program', attributes = {'time': 15, 'tired': False}),
            Event('test', attributes = {'time': 16, 'tired': False}),
            Event('shutdown computer', attributes = {'time': 17, 'tired': True})
        ])
        alignment = [(event, Event(event.activity_name if event.activity_name != 'test' else None,
                                   transition_id=event.activity_name if event.activity_name != 'test' else None)) for event in trace.events]
        expected_augment_alignment = [
            (Event('start computer', attributes={'time': 9, 'tired': False}),
             Event('start computer', transition_id='start computer', attributes={'time': 9, 'tired': False})),
            (Event('program', attributes={'time': 10, 'tired': False}),
             Event('program', transition_id='program', attributes={'time': 10, 'tired': False})),
            (Event('visit meeting', attributes={'time': 11, 'tired': True}),
             Event('visit meeting', transition_id='visit meeting', attributes={'time': 11, 'tired': True})),
            (Event('drink coffee', attributes={'time': 12, 'tired': True}),
             Event('drink coffee', transition_id='drink coffee', attributes={'time': 12, 'tired': True})),
            (Event('eat lunch', attributes={'time': 12, 'tired': False}),
             Event('eat lunch', transition_id='eat lunch', attributes={'time': 12, 'tired': False})),
            (Event('program', attributes={'time': 13, 'tired': False}),
             Event('program', transition_id='program', attributes={'time': 13, 'tired': False})),
            (Event('program', attributes={'time': 15, 'tired': False}),
             Event('program', transition_id='program', attributes={'time': 15, 'tired': False})),
            (Event('test', attributes={'time': 16, 'tired': False}),
             Event(None, attributes={'time': 16, 'tired': False})),
            (Event('shutdown computer', attributes={'time': 17, 'tired': True}),
             Event('shutdown computer', transition_id='shutdown computer', attributes={'time': 17, 'tired': True}))
        ]
        actual_augmented_alignment = augment_with_write_operations(alignment, self.net)

        self.maxDiff = None
        self.assertListEqual(expected_augment_alignment, actual_augmented_alignment)

    def test_alignment_explains_log_trace(self):
        self.assertFalse(alignment_explains_log_trace(
                [(Event('0'), Event(None)),
                 (Event(None), Event('p1_', transition_id='p1_')),
                 (Event('0'), Event(None)),
                 (Event('0'), Event(None)),
                 (Event('1'), Event(None)),
                 (Event('2'), Event(None)),
                 (Event('3'), Event(None)),
                 (Event('4'), Event('4', transition_id='4')),
                 (Event('5'), Event('5', transition_id='5')),
                 (Event(None), Event('p3_', transition_id='p3_'))],
                 Trace(0, [Event('0'),
                        Event('0'),
                        Event('0'),
                        Event('1'),
                        Event('2'),
                        Event('3'),
                        Event('4'),
                        Event('5'),
                        Event('4'),
                        Event('5'),
                        Event('6')])))
        self.assertTrue(alignment_explains_log_trace(
                [(Event('0'), Event(None)),
                 (Event(None), Event('p1_', transition_id='p1_')),
                 (Event('0'), Event(None)),
                 (Event('0'), Event(None)),
                 (Event('1'), Event(None)),
                 (Event('2'), Event(None)),
                 (Event('3'), Event(None)),
                 (Event('4'), Event('4', transition_id='4')),
                 (Event('5'), Event('5', transition_id='5')),
                 (Event('4'), Event('4', transition_id='4')),
                 (Event('5'), Event('5', transition_id='5')),
                 (Event(None), Event('p3_', transition_id='p3_')),
                 (Event('6'), Event('6', transition_id='6'))],
                 Trace(1, [Event('0'),
                        Event('0'),
                        Event('0'),
                        Event('1'),
                        Event('2'),
                        Event('3'),
                        Event('4'),
                        Event('5'),
                        Event('4'),
                        Event('5'),
                        Event('6')])))

    def test_balanced_conformance(self):
        trace = Trace(0, [
            Event('start computer', attributes = {'time': 9, 'tired': False}),
            Event('program', attributes = {'time': 10, 'tired': False}),
            Event('visit meeting', attributes = {'time': 11, 'tired': True}),
            Event('drink coffee', attributes = {'time': 12, 'tired': True}),
            Event('eat lunch', attributes = {'time': 12, 'tired': False}),
            Event('program', attributes = {'time': 13, 'tired': False}),
            Event('program', attributes = {'time': 15, 'tired': False}),
            Event('test', attributes = {'time': 16, 'tired': False}),
            Event('shutdown computer', attributes = {'time': 17, 'tired': True})
        ])
        expected_optimal_alignment = [
            (Event('start computer', attributes={'time': 9, 'tired': False}),
             Event('start computer', transition_id='start computer', attributes={'time': 9, 'tired': False})),
            (Event('program', attributes={'time': 10, 'tired': False}),
             Event('program', transition_id='program', attributes={'time': 10, 'tired': False})),
            (Event(None, attributes={}),
             Event('repeat', transition_id='repeat', attributes={})),
            (Event('visit meeting', attributes={'time': 11, 'tired': True}),
             Event('visit meeting', transition_id='visit meeting', attributes={'time': 11, 'tired': True})),
            (Event(None, attributes={}),
             Event('repeat', transition_id='repeat', attributes={})),
            (Event('drink coffee', attributes={'time': 12, 'tired': True}),
             Event('drink coffee', transition_id='drink coffee', attributes={'time': 12, 'tired': True})),
            (Event(None, attributes={}),
             Event('repeat', transition_id='repeat', attributes={})),
            (Event('eat lunch', attributes={'time': 12, 'tired': False}),
             Event('eat lunch', transition_id='eat lunch', attributes={'time': 12, 'tired': False})),
            (Event(None, attributes={}),
             Event('repeat', transition_id='repeat', attributes={})),
            (Event('program', attributes={'time': 13, 'tired': False}),
             Event('program', transition_id='program', attributes={'time': 13, 'tired': False})),
            (Event(None, attributes={}),
             Event('repeat', transition_id='repeat', attributes={})),
            (Event('program', attributes={'time': 15, 'tired': False}),
             Event('program', transition_id='program', attributes={'time': 15, 'tired': False})),
            (Event('test', attributes={'time': 16, 'tired': False}),
             Event(None, attributes={'time': 16, 'tired': False})),
            (Event('shutdown computer', attributes={'time': 17, 'tired': True}),
             Event('shutdown computer', transition_id='shutdown computer', attributes={'time': 17, 'tired': True}))
        ]
        actual_optimal_alignment = balanced_conformance(
                self.net, self.initial_marking, self.final_marking, trace)
        self.maxDiff = None
        self.assertListEqual(expected_optimal_alignment,
                             actual_optimal_alignment)

        actual_optimal_alignment = balanced_conformance(
            self.net, self.initial_marking, self.final_marking, trace)
        self.assertListEqual(expected_optimal_alignment,
                             actual_optimal_alignment)

        #now the same without guards
        for transition in self.net.transitions.values():
            transition.set_guard_function(None)
        actual_optimal_alignment = balanced_conformance(
            self.net, self.initial_marking, self.final_marking, trace)
        self.assertListEqual(expected_optimal_alignment,
                             actual_optimal_alignment)

    def test_balanced_conformance_with_model_move_at_start(self):
        trace = Trace(0, [
            Event('A')
        ])
        minimal_net = DataPetriNet()
        start = minimal_net.add_place(Place.with_id_label('start'))
        middle = minimal_net.add_place(Place.with_id_label('middle'))
        end = minimal_net.add_place(Place.with_id_label('end'))
        t0 = minimal_net.add_transition(Transition('0', visible=False))
        tA = minimal_net.add_transition(Transition('A', visible=True))
        minimal_net.add_connection(start, t0, middle)
        minimal_net.add_connection(middle, tA, end)
        initial_marking = {'start': 1, 'middle': 0, 'end': 0}
        final_marking = {'start': 0, 'middle': 0, 'end': 1}
        expected_optimal_alignment = [
            (Event(None),
             Event('0', transition_id='0')),
            (Event('A'),
             Event('A', transition_id='A'))
        ]
        actual_optimal_alignment = balanced_conformance(
                minimal_net, initial_marking, final_marking, trace)
        self.maxDiff = None
        self.assertListEqual(expected_optimal_alignment,
                             actual_optimal_alignment)

        actual_optimal_alignment = balanced_conformance(
            minimal_net, initial_marking, final_marking, trace)
        self.assertListEqual(expected_optimal_alignment,
                             actual_optimal_alignment)

    def test_cost_function(self):
        optimal_alignment = [
            (Event('start computer', attributes={'time': 9, 'tired': False}),
             Event('start computer', transition_id='start computer', attributes={'time': 9, 'tired': False})),
            (Event('program', attributes={'time': 10, 'tired': False}),
             Event('program', transition_id='program', attributes={'time': 10, 'tired': False})),
            (Event(None, attributes={}),
             Event('repeat', transition_id='repeat', attributes={})),
            (Event('visit meeting', attributes={'time': 11, 'tired': True}),
             Event('visit meeting', transition_id='visit meeting', attributes={'time': 11, 'tired': True})),
            (Event(None, attributes={}),
             Event('repeat', transition_id='repeat', attributes={})),
            (Event('drink coffee', attributes={'time': 12, 'tired': True}),
             Event('drink coffee', transition_id='drink coffee', attributes={'time': 12, 'tired': True})),
            (Event(None, attributes={}),
             Event('repeat', transition_id='repeat', attributes={})),
            (Event('eat lunch', attributes={'time': 12, 'tired': False}),
             Event('eat lunch', transition_id='eat lunch', attributes={'time': 12, 'tired': False})),
            (Event(None, attributes={}),
             Event('repeat', transition_id='repeat', attributes={})),
            (Event('program', attributes={'time': 13, 'tired': False}),
             Event('program', transition_id='program', attributes={'time': 13, 'tired': False})),
            (Event(None, attributes={}),
             Event('repeat', transition_id='repeat', attributes={})),
            (Event('program', attributes={'time': 15, 'tired': False}),
             Event('program', transition_id='program', attributes={'time': 15, 'tired': False})),
            (Event('test', attributes={'time': 16, 'tired': False}),
             Event(None, attributes={'time': 16, 'tired': False})),
            (Event('shutdown computer', attributes={'time': 17, 'tired': True}),
             Event('shutdown computer', transition_id='shutdown computer', attributes={'time': 17, 'tired': True}))
        ]
        #Due to the log move ('test', None), cost is 1 and not 0
        self.assertEqual(1, cost_function(optimal_alignment, self.net))

    def test_product_net(self):
        trace = Trace(0, [
            Event('start computer', attributes = {'time': 9, 'tired': False}),
            Event('program', attributes = {'time': 10, 'tired': False}),
            Event('visit meeting', attributes = {'time': 11, 'tired': True}),
            Event('drink coffee', attributes = {'time': 12, 'tired': True}),
            Event('eat lunch', attributes = {'time': 12, 'tired': False}),
            Event('program', attributes = {'time': 13, 'tired': False}),
            Event('program', attributes = {'time': 15, 'tired': False}),
            Event('test', attributes = {'time': 16, 'tired': False}),
            Event('shutdown computer', attributes = {'time': 17, 'tired': True})
        ])
        product_net, initial_marking, final_marking, transition_costs = create_product_net(self.net, trace)
        with open('prolothar_tests/resources/product_net.txt', 'r') as f:
            self.assertCountEqual(f.read().strip().split('\n'),
                                 product_net.plot(view=False).strip().split('\n'))
        for place in product_net.places.values():
            self.assertTrue(place.id in initial_marking,
                            'place %s should be in initial_marking' % place.id)
            self.assertTrue(place.id in final_marking,
                            'place %s should be in final_marking' % place.id)
        self.assertEqual(0, transition_costs['repeat'],
                         msg='invisible transition "repeat" should cost 0')

    def test_product_net_with_duplicate_activity_in_model(self):
        trace = Trace(0, [
            Event('A'),
            Event('B'),
        ])

        model = DataPetriNet()
        p_start = model.add_place(Place.with_empty_label('start'))
        p_1 = model.add_place(Place.with_empty_label('p1'))
        p_2 = model.add_place(Place.with_empty_label('p2'))
        p_3 = model.add_place(Place.with_empty_label('p3'))
        p_4 = model.add_place(Place.with_empty_label('p4'))
        p_end = model.add_place(Place.with_empty_label('end'))
        t_a_1 = model.add_transition(Transition('A1', 'A'))
        t_a_2 = model.add_transition(Transition('A2', 'A'))
        t_b = model.add_transition(Transition('B'))
        t_c = model.add_transition(Transition('C'))
        t_end_1 = model.add_transition(Transition('t_end_1', visible=False))
        t_end_2 = model.add_transition(Transition('t_end_2', visible=False))
        model.add_connection(p_start, t_a_1, p_1)
        model.add_connection(p_1, t_b, p_2)
        model.add_connection(p_2, t_end_1, p_end)
        model.add_connection(p_start, t_a_2, p_3)
        model.add_connection(p_3, t_c, p_4)
        model.add_connection(p_4, t_end_2, p_end)

        product_net, initial_marking, final_marking, transition_costs = create_product_net(model, trace)
        self.assertEqual(5, len([t for t in product_net.transitions.values() if t.label == 'A']))

if __name__ == '__main__':
    unittest.main()