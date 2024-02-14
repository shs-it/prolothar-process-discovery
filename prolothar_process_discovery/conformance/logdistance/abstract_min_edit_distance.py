# -*- coding: utf-8 -*-

from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.conformance.logdistance.trace_to_characters_translator import TraceToCharacterTranslator
from strsimpy.levenshtein import Levenshtein
import pandas as pd

from abc import ABC, abstractmethod

class AbstractMinEditDistance(ABC):

    def __init__(self):
        self.__trace_to_character_translator = TraceToCharacterTranslator()
        self.__levenshtein = Levenshtein()

    def compute(self, log1: EventLog, log2: EventLog) -> int:
        if log1.get_nr_of_traces() != log2.get_nr_of_traces():
            raise ValueError('logs must have the same number of traces')
        return self._compute_distance_from_trace_distance_matrix(
                self.__compute_trace_distance_matrix(log1, log2))

    @abstractmethod
    def _compute_distance_from_trace_distance_matrix(
            self, trace_distance_matrix) -> int:
        pass

    def __compute_trace_distance_matrix(self, log1: EventLog, log2: EventLog):
        distance_matrix = {}
        translated_traces1 = [
                self.__trace_to_character_translator.translate_trace(trace)
                for trace in log1.traces]
        translated_traces2 = [
                self.__trace_to_character_translator.translate_trace(trace)
                for trace in log2.traces]
        for i,trace1 in enumerate(translated_traces1):
            distance_row = {}
            for j,trace2 in enumerate(translated_traces2):
                distance_row[j] = \
                    self.__levenshtein.distance(trace1, trace2)
            distance_matrix[i] = distance_row
        return pd.DataFrame.from_dict(distance_matrix).to_numpy()

