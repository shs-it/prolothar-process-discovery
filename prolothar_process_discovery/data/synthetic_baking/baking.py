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
from random import Random

from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph
from prolothar_common.models.eventlog import EventLog, Trace, Event

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.pattern.subgraph import SubGraph
from prolothar_process_discovery.discovery.proseqo.pattern.clustering import Clustering

from typing import List

"""
See http://confluence.int.shsservices.de/display/KIINNO/Synthetisches+Log
"""

model_without_clustering = PatternDfg()

model_without_clustering.add_count('Start', 'Make Dough')
model_without_clustering.add_count('Make Dough', 'Bake')
model_without_clustering.add_count('Bake', 'Enjoy')
model_without_clustering.add_count('Enjoy', 'End')

model_without_clustering.add_pattern('Make Dough', Choice([
        Singleton('Make Sponge'),
        Singleton('Make Yeast Dough'),
        Singleton('Make Biscuit')]))

bake_pattern_dfg = PatternDfg()
bake_pattern_dfg.add_count('Put into Oven', 'Watch TV')
bake_pattern_dfg.add_count('Put into Oven', 'Read a Book')
bake_pattern_dfg.add_count('Watch TV', 'Check Time')
bake_pattern_dfg.add_count('Read a Book', 'Check Time')
bake_pattern_dfg.add_count('Check Time', 'Watch TV')
bake_pattern_dfg.add_count('Check Time', 'Read a Book')
bake_pattern_dfg.add_count('Check Time', 'Take out of the Oven')
model_without_clustering.add_pattern('Bake', SubGraph(
        bake_pattern_dfg, ['Put into Oven'], ['Take out of the Oven']))

model_without_clustering.add_pattern('Enjoy', Sequence([
        Optional(Singleton('Sprinkle with Icing Sugar')),
        Singleton('Eat'),
        Singleton('Smile')]))

model_without_clustering_expanded = model_without_clustering.expand()

###############################
# Make Sponge
sponge_model = DirectlyFollowsGraph()
sponge_model.add_count('Start', 'Add Butter')
sponge_model.add_count('Add Butter', 'Add Sugar')
sponge_model.add_count('Add Sugar', 'Beat up Foamy')
sponge_model.add_count('Beat up Foamy', 'Add Eggs')
sponge_model.add_count('Add Eggs', 'Stir')
sponge_model.add_count('Stir', 'Add Baking Powder')
sponge_model.add_count('Add Baking Powder', 'Stir')
sponge_model.add_count('Stir', 'Add Flour')
sponge_model.add_count('Add Flour', 'Stir')
sponge_model.add_count('Stir', 'Add Milk')
sponge_model.add_count('Add Milk', 'Stir')
sponge_model.add_count('Add Milk', 'End')
# Make Yeast Dough
yeast_dough_model = DirectlyFollowsGraph()
yeast_dough_model.add_count('Start', 'Add Milk')
yeast_dough_model.add_count('Add Milk', 'Add Sugar')
yeast_dough_model.add_count('Add Sugar', 'Add Yeast')
yeast_dough_model.add_count('Add Yeast', 'Stir in Flour')
yeast_dough_model.add_count('Stir in Flour', 'End')
# Make Biscuit
biscuit_model = DirectlyFollowsGraph()
biscuit_model.add_count('Start', 'Add Eggs')
biscuit_model.add_count('Add Eggs', 'Add Sugar')
biscuit_model.add_count('Add Sugar', 'Beat up Foamy')
biscuit_model.add_count('Beat up Foamy', 'Add Flour')
biscuit_model.add_count('Add Flour', 'Fold in')
biscuit_model.add_count('Fold in', 'End')
# clustering model dict
clustering_model_dict = {
    'Make Sponge': sponge_model,
    'Make Yeast Dough': yeast_dough_model,
    'Make Biscuit': biscuit_model
}


def generate_log(nr_of_traces: int,
                 use_clustering_model=False,
                 noise_probability_remove_activity: float=0,
                 random_seed: int = None) -> EventLog:
    random = Random(random_seed)
    if noise_probability_remove_activity < 0 or noise_probability_remove_activity >= 1:
        raise ValueError('noise_probability_remove_activity must be in [0,1)')
    log = EventLog()
    for i in range(nr_of_traces):
        log.add_trace(generate_trace(
                i, use_clustering_model, random,
                noise_probability_remove_activity=noise_probability_remove_activity))
    log.join_sucessive_events_with_same_activity()
    return log

def generate_trace(trace_id: int, use_clustering_model: bool, random: Random,
                   noise_probability_remove_activity=0):
    events = []

    end_activities = model_without_clustering_expanded.get_sink_activities()

    current_activity = 'Start'
    events.append(Event(current_activity))
    while current_activity not in end_activities:
        current_activity = random.choice(
            model_without_clustering_expanded.get_following_activities(current_activity))
        if (not use_clustering_model or
            current_activity not in clustering_model_dict):
            if (random.uniform(0, 1) >= noise_probability_remove_activity or
                current_activity == 'End'):
                events.append(Event(current_activity))
        else:
            _add_generated_events_from_clustering_model(
                    events, clustering_model_dict[current_activity],
                    noise_probability_remove_activity, random)

    return Trace(trace_id, events, attributes={'id': trace_id})

def _add_generated_events_from_clustering_model(
        events: List[Event], model: DirectlyFollowsGraph,
        noise_probability_remove_activity: float, random: Random):
    current_activity = 'Start'
    while True:
        current_activity = random.choice(
                model.get_following_activities(current_activity))
        if current_activity != 'End':
            if random.uniform(0, 1) >= noise_probability_remove_activity:
                events.append(Event(current_activity))
        else:
            break

def get_ideal_pattern_graph_with_clustering(log: EventLog) -> PatternDfg:
    model = model_without_clustering.copy()
    model.remove_node('Start')

    trace_to_community_index_dict = {}

    for trace in log.traces:
        if trace.get_first_index_of_first_matching_activity(set([
                'Add Butter', 'Stir'])) >= 0:
            trace_to_community_index_dict[trace] = 0
        elif trace.get_first_index_of_first_matching_activity(set([
                'Add Yeast', 'Stir in Flour'])) >= 0:
            trace_to_community_index_dict[trace] = 1
        elif trace.get_first_index_of_first_matching_activity(set([
                'Fold in'])) >= 0:
            trace_to_community_index_dict[trace] = 2
        else:
            raise ValueError()

    sponge_community = PatternDfg.create_from_dfg(sponge_model)
    sponge_community = sponge_community.fold({Sequence.from_activity_list([
            'Start', 'Add Butter', 'Add Sugar', 'Beat up Foamy', 'Add Eggs'])})

    sponge_community = SubGraph(sponge_community,
                                ['[Start,Add Butter,Add Sugar,Beat up Foamy,Add Eggs]'],
                                ['Add Milk'])
    sponge_community.remove_activity('End')

    communities = [sponge_community,
                   Sequence.from_activity_list([
                           'Start', 'Add Milk', 'Add Sugar', 'Add Yeast',
                           'Stir in Flour']),
                   Sequence.from_activity_list([
                           'Start', 'Add Eggs', 'Add Sugar', 'Beat up Foamy',
                           'Add Flour', 'Fold in'])]

    clustering = Clustering(communities, trace_to_community_index_dict)

    model.add_pattern('Make Dough', clustering)

    for node in list(model.get_nodes()):
        if node.activity != node.pattern.get_activity_name():
            model.rename_activity(node.activity, node.pattern.get_activity_name())

    return model



if __name__ == '__main__':
    for noise_level in [0, 0.01, 0.02, 0.03, 0.04, 0.05]:
        log = generate_log(100, use_clustering_model=True,
                           noise_probability_remove_activity=noise_level,
                           random_seed=42)
        with open(('experiments/data/synthetic_baking/'
                   '%d_traces_with_clustering_noise_%r.csv') % (
                           log.get_nr_of_traces(), noise_level),
                   'w') as csv_writer:
            log.write_to_csv(csv_writer)




