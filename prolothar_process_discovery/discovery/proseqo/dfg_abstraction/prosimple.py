from prolothar_common.models.eventlog import EventLog
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg

from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.dfg_abstraction_strategy import DfgAbstractionStrategy
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.union import Union
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.prune_with_mdl import PruneWithMdl
from prolothar_process_discovery.discovery.proseqo.dfg_abstraction.proseqo import Proseqo
from prolothar_process_discovery.discovery.proseqo.edge_removal.termination_criterion import MaxAverageDegree


class ProSimple(DfgAbstractionStrategy):
    """
    algorithm for our paper. this class is a facade to implemented stuff in
    this package. it uses the union strategy, the iterative best pattern
    strategy and prune_with_mdl to mine a model for processes with sequences,
    choices, loops, optionalsthat can include noise.
    """

    def __init__(self, nr_of_workers: int = -1, alpha: float = 1.5):
        self.__nr_of_workers = nr_of_workers
        self.__alpha = alpha

    def mine_dfg(self, log: EventLog, dfg: PatternDfg, verbose: bool = False) -> PatternDfg:
        if self.__nr_of_workers > 0:
            proseqo = Proseqo(max_nr_of_workers=self.__nr_of_workers)
        else:
            proseqo = Proseqo()
        pattern_search_strategy = Union([
            proseqo,
            PruneWithMdl(
                MaxAverageDegree(self.__alpha),
                evaluation_limit='nodes',
                recompute_gain_in_every_iteration=False,
                use_mdl_estimations = True,
                reweight_edges = True,
                allow_multiprocessing = self.__nr_of_workers != 1),
            proseqo
        ])
        return pattern_search_strategy.mine_dfg(log, dfg, verbose=verbose)

    def __repr__(self) -> str:
        return f'ProSimple(alpha={self.__alpha})'