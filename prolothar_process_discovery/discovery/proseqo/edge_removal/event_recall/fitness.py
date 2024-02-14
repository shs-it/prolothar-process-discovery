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

from prolothar_process_discovery.discovery.proseqo.edge_removal.event_recall.event_recall import EventRecall

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
import prolothar.pm.pm4py.pm4py_utils as pm4py_utils
from pm4py.evaluation.replay_fitness import factory as replay_factory

class FitnessEventRecall(EventRecall):
    """implementation of EventRecall that rewards uses petri net fitness
    as the recall definition
    """

    def compute(self, dfg: DirectlyFollowsGraph, log: EventLog) -> float:
        log_pm4py = pm4py_utils.convert_eventlog_to_pm4py(log)

        petri_net, initial_marking, final_marking = \
            pm4py_utils.convert_data_petri_net_to_pm4py(
                PatternDfg.create_from_dfg(dfg).convert_to_petri_net())

        return replay_factory.apply(
                log_pm4py, petri_net, initial_marking,
                final_marking)['averageFitness']