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

from abc import ABC, abstractmethod

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg

class TerminationCriterion(ABC):
    @abstractmethod
    def should_terminate(self, initial_dfg: PatternDfg,
                         current_dfg: PatternDfg,
                         verbose: bool = False) -> bool:
        pass

class MaxNumberOfEdgesRemoved(TerminationCriterion):
    """edge removal is stopped if N edges have been removed"""
    def __init__(self, n: int):
        self.__n = n
    def should_terminate(self, initial_dfg: PatternDfg,
                         current_dfg: PatternDfg,
                         verbose: bool = False) -> bool:
        return (initial_dfg.get_nr_of_edges() -
                current_dfg.get_nr_of_edges() >= self.__n)

class NrOfCalls(TerminationCriterion):
    """edge removal is stopped if should_terminate has been called more
    than N times"""
    def __init__(self, n: int):
        self.__n = n
        self.__i = 0
    def should_terminate(self, initial_dfg: PatternDfg,
                         current_dfg: PatternDfg,
                         verbose: bool = False) -> bool:
        self.__i += 1
        return self.__i > self.__n

class MaxGraphDensityReached(TerminationCriterion):
    """edge removal is stopped if the graph density is lower or equal than X"""
    def __init__(self, max_graph_density: float):
        self.__max_graph_density = max_graph_density
    def should_terminate(self, initial_dfg: PatternDfg,
                         current_dfg: PatternDfg,
                         verbose: bool = False) -> bool:
        if current_dfg.get_nr_of_nodes() > 0:
            current_density = (current_dfg.get_nr_of_edges() /
                               (current_dfg.get_nr_of_nodes() ** 2))
        else:
            current_density = 0
        if verbose:
            print('current density: %r (max: %r)' % (current_density,
                                                     self.__max_graph_density))
        return current_density <= self.__max_graph_density

class MaxAverageDegree(TerminationCriterion):
    """edge removal is stopped if the average degree in the graph is lower or
    equal than X"""
    def __init__(self, max_average_degree: float):
        self.__max_average_degree = max_average_degree
    def should_terminate(self, initial_dfg: PatternDfg,
                         current_dfg: PatternDfg,
                         verbose: bool = False) -> bool:
        if current_dfg.get_nr_of_nodes() > 0:
            current_degree = (current_dfg.get_nr_of_edges() /
                               (current_dfg.get_nr_of_nodes()))
        else:
            current_degree = 0
        if verbose:
            print('current degree: %r (max: %r)' % (current_degree,
                                                     self.__max_average_degree))
        return current_degree <= self.__max_average_degree
    def __repr__(self) -> str:
        return 'MaxAverageDegree(%r)' % self.__max_average_degree
