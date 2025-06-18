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
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_process_discovery.discovery.proseqo.pattern.sequence import Sequence
from prolothar_process_discovery.discovery.proseqo.pattern.choice import Choice
from prolothar_process_discovery.discovery.proseqo.pattern.optional import Optional
from prolothar_process_discovery.discovery.proseqo.pattern.singleton import Singleton
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.candidates.generator.pattern_candidate_generator import PatternCandidateGenerator
from prolothar_process_discovery.discovery.proseqo.structural_dfg_patterns.isolated_sequences import find_isolated_sequences_in_dfg
from prolothar_common.models.directly_follows_graph import DirectlyFollowsGraph

from prolothar_process_discovery.discovery.proseqo.mdl_score import compute_mdl_score

from typing import Iterable

import pandas as pd

class NoisySequenceCandidateGenerator(PatternCandidateGenerator):
    """finds noisy sequence candidates in a pattern_dfg"""

    def _generate_patterns(
            self, log: EventLog, dfg: PatternDfg,
            pattern_dfg: PatternDfg) -> Iterable[Sequence]:
        dfg = PatternDfg.create_from_event_log(log)
        #makes sure we call this generator only once
        if dfg != pattern_dfg:
            return []

        eventually_follows_df = self.__create_eventually_follows_dataframe(log)
        intersection_df = self.__compute_intersection_df(
                eventually_follows_df)

        candidates = []

        for row in intersection_df.iterrows():
            noisy_activity_set = row[0]
            linear_activity_set = row[1]['activity']
            for noisy_activity in noisy_activity_set:
                linear_activity_set.update(
                        dfg.get_following_activities(noisy_activity))
            linear_activity_set.difference_update(noisy_activity_set)

            sublog = log.copy()
            sublog.filter_activities(linear_activity_set)
            sublog.keep_first_occurence_of_activity_only()

            sequence = self.__derive_sequence_from_sublog(sublog)
            if sequence is not None:
                sequence.special_noise_set = noisy_activity_set
                candidates.append(sequence)

        return candidates

    def __derive_sequence_from_sublog(self, sublog: EventLog) -> Sequence:
        subdfg = PatternDfg.create_from_event_log(sublog)
        sequence = self.__derive_sequence_from_subpdfg(subdfg, sublog)
        if sequence is None:
            return None
        return self.__find_best_sequence_variant(sequence, sublog)

    def __derive_sequence_from_subpdfg(
            self, subdfg: PatternDfg, sublog: EventLog) -> Sequence:
        subdfg = self.__compress_with_sequences(subdfg)

        sequence_elements = []
        while subdfg.get_nr_of_nodes() > 0:
            current_source_nodes = subdfg.get_source_nodes()
            if not current_source_nodes:
                return None
            next_element = Choice([node.pattern
                                   for node in current_source_nodes])
            next_element = next_element.without_degeneration()[0]
            sequence_elements.append(next_element)
            for node in current_source_nodes:
                subdfg.remove_node(node.activity)

        sequence = Sequence(sequence_elements)
        sequence.merge_subpatterns()
        return sequence

    def __compute_intersection_df(self, eventually_follows_df):
        intersection_df = eventually_follows_df[['activity', 'inter']]
        intersection_df = intersection_df[intersection_df['inter'] != set()]
        intersection_df = intersection_df.groupby('inter').aggregate(
                lambda tdf: set(tdf.tolist()))
        return intersection_df[intersection_df['activity'].str.len() > 1]

    def __create_eventually_follows_dataframe(self, log: EventLog) -> pd.DataFrame:
        eventually_follows_graph = \
            DirectlyFollowsGraph.build_eventually_follows_on_first_occurence_graph(
                    log)
        data = []
        for node in eventually_follows_graph.get_nodes():
            pre = frozenset(
                    eventually_follows_graph.get_preceeding_activities(
                            node.activity))
            post = frozenset(
                    eventually_follows_graph.get_following_activities(
                            node.activity))
            data.append((
                node.activity, pre, post,
                frozenset(pre.intersection(post))
            ))
        return pd.DataFrame(data, columns=['activity', 'pre', 'post', 'inter'])

    def __compress_with_sequences(self, dfg: PatternDfg):
        sequences = find_isolated_sequences_in_dfg(dfg)
        while sequences:
            dfg = dfg.fold(sequences)
            sequences = find_isolated_sequences_in_dfg(dfg)
        return dfg

    def __find_best_sequence_variant(
            self, sequence: Sequence, sublog: EventLog):
        sublog = sublog.copy()
        sublog.add_start_activity_to_every_trace('__seqtempstart__')
        sublog.add_end_activity_to_every_trace('__seqtempend__')
        subdfg = PatternDfg.create_from_event_log(sublog)

        sequence = sequence.copy()
        sequence.pattern_list = [Singleton('__seqtempstart__')] + \
                                sequence.pattern_list + \
                                [Singleton('__seqtempend__')]
        sequence.clear_cache()

        lowest_mdl = compute_mdl_score(sublog, subdfg.fold({sequence}))
        changed = True
        while changed:
            changed = False
            i = 1
            while i < sequence.get_nr_of_subpatterns() - 1:
                sequence_with_optional_i = sequence.copy()
                sequence_with_optional_i.pattern_list[i] = Optional(
                        sequence_with_optional_i.pattern_list[i])
                sequence_with_optional_i.clear_cache()
                candidate_mdl = compute_mdl_score(sublog, subdfg.fold({
                        sequence_with_optional_i}))
                if candidate_mdl < lowest_mdl:
                    lowest_mdl = candidate_mdl
                    sequence = sequence_with_optional_i
                    changed = True
                i += 1

        sequence.pattern_list = sequence.pattern_list[1:-1]
        sequence.clear_cache()
        return sequence