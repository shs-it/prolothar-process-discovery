# Prolothar Process Discovery

Algorithms to discover process behavior from data mining on sequential data such as process logs.

Based on the publication
> Boris Wiegand, Dietrich Klakow, and Jilles Vreeken.
> **Mining easily understandable models from complex event logs.**
> In: *Proceedings of the SIAM International Conference on Data Mining (SDM), Virtual Event.* 2021, pp. 244-252.

## Prerequisites

Python 3.11+

## Usage

If you want to run the algorithms on your own data, follow the steps below.

### Installing

```bash
pip install prolothar-process-discovery
```

### Creating or reading an EventLog

Option 1: you can create an EventLog from a pandas dataframe

```python
# 1) there must be a header line
# 2) each line belongs to one event
# 3) there is one column containing the case ID
# 4) there is one column containing the activity name of the event
# 5) there can be columns for trace and event attributes
import pandas as pd
eventlog = EventLog.create_from_pandas_df(
      pd.read_csv('path/to/eventlog.csv', delimiter=','),
      'CaseId', 'Activity',
      trace_attribute_columns=['Customer'],
      event_attribute_columns=['Duration']
)
```

Option 2: you can create an EventLog from .xes with the help of the pm4py package

```python
from pm4py.objects.log.importer.xes import importer as xes_import_factory
import prolothar_common.pm4py_utils as pm4py_utils
xes = xes_import_factory.apply('path/to/eventlog.xes.gz')
eventlog = pm4py_utils.convert_pm4py_log(xes)
```

Option 3: you can create an EventLog manually

```python
from prolothar_common.models.eventlog import EventLog, Trace, Event
eventlog = EventLog()
#case ID (0 in the example) can be any hashable type, e.g. int or string. must be unique.
eventlog.add_trace(Trace(0, [
      Event('start computer', attributes={'user': 'alice'}),
      Event('drink coffee', attributes={'milk': 'yes', 'grams_of_sugar': 5}),
]))
```

### Discovering a PatternGraph

```python
from prolothar_process_discovery.discovery import Proseqo
from prolothar_process_discovery.discovery import ProSimple
from prolothar_process_discovery.discovery.proseqo.pattern_dfg import PatternDfg

directly_follows_graph = PatternDfg.create_from_event_log(eventlog)

pattern_graph = Proseqo().mine_dfg(eventlog, directly_follows_graph, verbose=True)
pattern_graph.plot()

pattern_graph = ProSimple().mine_dfg(eventlog, directly_follows_graph, verbose=True)
# we can also plot to a file
pattern_graph.plot(filepath='path/to/your/file', filetype: str='pdf', view=False)
```

If you get an error stating that parameter "last_covered_activity" is unexpectedly of type "None",
add a common start and a common end activity to all traces:

```python
log.add_start_activity_to_every_trace('START')
log.add_end_activity_to_every_trace('END')
```

## Development

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Additional Prerequisites
- make (optional)

### Running the tests

```bash
make test
```

### Deployment

1. Change the version in version.txt
2. Build and publish the package on pypi by
```bash
make clean_package
make package && make publish
```
3. Create and push a tag for this version by
```bash
git tag -a [version] -m "describe this version"
git push --tags
```

## Versioning

We use [SemVer](http://semver.org/) for versioning.

## Authors

If you have any questions, feel free to ask one of our authors:

* **Boris Wiegand** - boris.wiegand@stahl-holding-saar.de
