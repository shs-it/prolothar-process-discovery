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

from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg
from prolothar_common.models.eventlog import Trace
from prolothar_process_discovery.discovery.proseqo.greedy_cover import compute_cover
from prolothar_process_discovery.discovery.proseqo.cover_streams.move_stream import MoveStream

import pandas as pd

from typing import List

def count_moves(trace_list: List[Trace], pattern_dfg: PatternDfg):
    return pd.DataFrame(data=[
        _count_moves_for_traces(trace, pattern_dfg) for trace in trace_list
    ], columns=['Trace',
                '# Moves',
                '# Sync Moves',
                '# Log Moves',
                '# Model Moves'])

def _count_moves_for_traces(trace: Trace, pattern_dfg: PatternDfg):
    cover = compute_cover([trace], pattern_dfg)
    move_code_counter = cover.move_stream.count_move_codes()
    return [trace.to_activity_list(),
            sum(move_code_counter.values()),
            move_code_counter[MoveStream.SYNCHRONOUS_MOVE],
            move_code_counter[MoveStream.LOG_MOVE],
            move_code_counter[MoveStream.MODEL_MOVE]]