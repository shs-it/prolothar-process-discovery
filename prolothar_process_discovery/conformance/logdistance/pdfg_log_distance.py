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

class PatternDfgLogdistance():
    """computes the distance between a log and a model (pattern-dfg)
    by generating traces from the model and comparing these traces with the
    given log
    """

    def __init__(self , logdistance):
        """creates a new instance

        Args:
            - logdistance:
                used to compute the distance between the generated log by
                the model and the log from which the model was mined
        """
        self.__logdistance = logdistance

    def compute(self, model: PatternDfg, log: EventLog, random_seed: int = None):
        generated_log = model.generate_log(
                log.get_nr_of_traces(), random_seed = random_seed,
                start_activities = set(
                        p.get_activity_name()
                        for a in log.compute_set_of_start_activities()
                        for p in model.get_patterns_with_activity(a)),
                end_activities = set(
                        p.get_activity_name()
                        for a in log.compute_set_of_end_activities()
                        for p in model.get_patterns_with_activity(a)))
        return self.__logdistance.compute(log, generated_log)
