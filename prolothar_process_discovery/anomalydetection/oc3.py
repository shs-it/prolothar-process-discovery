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
from typing import List
import matplotlib.pyplot as plt
from math import sqrt
from prolothar_common.experiments.statistics import Statistics
from tqdm import tqdm

class Oc3(ABC):
    """
    interface for implementations of "The Odd One Out" for MDL based
    anomaly detection.

    https://pdfs.semanticscholar.org/7778/6bb6de48bcf0ffa7ebe4827f3b11b72f8546.pdf?_ga=2.227867933.1490009918.1599569008-1966438552.1513161256
    """

    def __init__(
            self, dataset: List, compute_encoded_length_isolated: bool = True,
            devide_by_instance_length: bool = False):
        self.__dataset = [instance for instance in dataset]
        self.__compute_encoded_length_isolated = compute_encoded_length_isolated
        if not compute_encoded_length_isolated:
            self.__encoded_length_of_dataset = self.compute_encoded_length_of_dataset(
                self.__dataset)
        self.__devide_by_instance_length = devide_by_instance_length

    def plot_data_encoding_histogram(self):
        """
        plots the histogram for the encoded length of instances in the given
        dataset
        """
        encoded_lengths = [self.compute_encoded_length(instance)
                           for instance in self.__dataset]
        plt.hist(encoded_lengths, bins = int(sqrt(len(encoded_lengths))))
        plt.show(block=False)

    def train_by_cantellis_inequality(
            self, confidence_level: float) -> 'TrainedOc3':
        """
        uses Cantelli's inequality to determine theta.

        Parameters
        ----------
        confidence_level : float
            number in interval (0,1]. the lower the more instances are seen
            as outliers

        Raises
        ------
        ValueError
            if confidence value is <= 0 or > 1.

        Returns
        -------
        a trained anomaly detector
        """
        if confidence_level <= 0 or confidence_level > 1:
            raise ValueError('confidence_level must be in (0,1] but was %r' %
                             confidence_level)
        statistics = Statistics()
        for instance in tqdm(self.__dataset):
            statistics.push(self.compute_encoded_length(instance))

        k = sqrt(1/confidence_level - 1)
        theta = statistics.mean() + k * statistics.stddev()
        return TrainedOc3(self, theta)

    def get_dataset(self) -> List:
        return self.__dataset

    def compute_encoded_length(self, instance) -> float:
        """computes L(D|M)"""
        if self.__compute_encoded_length_isolated:
            encoded_length = self._compute_encoded_length_of_instance(instance)
        else:
            encoded_length = (
                self._compute_encoded_length_of_additional_instance(
                    self.__dataset, instance)
                - self.__encoded_length_of_dataset)
        if self.__devide_by_instance_length:
            encoded_length = encoded_length / len(instance)
        return encoded_length

    @abstractmethod
    def compute_encoded_length_of_dataset(self, dataset: List) -> float:
        """computes L(D|M)"""

    @abstractmethod
    def _compute_encoded_length_of_instance(self, instance) -> float:
        """computes L(instance|M)"""

    @abstractmethod
    def _compute_encoded_length_of_additional_instance(
            self, dataset_without_instance: List, instance) -> float:
        """computes L(D+instance|M)"""


class TrainedOc3():
    """
    a trained anomaly detector based on MDL. An instance is an anomaly
    iff L(D|M) > theta. "Trained" means "theta" has been set
    """

    def __init__(self, oc3: Oc3, theta: float):
        self.__oc3 = oc3
        self.__theta = theta

    def is_anomaly(self, instance) -> bool:
      """
      returns True if L(D|M) > self.__theta
      """
      return self.__oc3.compute_encoded_length(instance) > self.__theta

    def compute_encoded_length(self, instance) -> float:
        """computes L(D|M)"""
        return self.__oc3.compute_encoded_length(instance)

    def get_theta(self) -> float:
        return self.__theta