from collections import OrderedDict
from releasetasks.util import sort_tasks, graph_to_tasks, add_atomic_task, \
    inject_dummy_tasks


def test_sort_tasks():
    unsorted = OrderedDict({
        'a': {'dependencies': ['b']},
        'b': {'dependencies': ['c']},
        'c': {},
    })
    sorted_tasks = sort_tasks(unsorted)
    assert sorted_tasks.keys() == ['c', 'b', 'a']


def test_graph_to_tasks():
    graph = {
        "tasks": [
            {
                "requires": ["a"],
                "taskId": "b",
                "task": {"payload": {}, "provisionerId": "m"}
            }
        ]
    }
    expected = OrderedDict(
        [('b', {'dependencies': ['a'], 'payload': {}, 'provisionerId': 'm'})])
    assert graph_to_tasks(graph) == expected


def test_graph_to_tasks_exit_status():
    graph = {
        "tasks": [
            {
                "requires": ["a"],
                "taskId": "b",
                "task": {"payload": {}, "provisionerId": "aws-provisioner-v1"}
            }
        ]
    }
    expected = OrderedDict(
        [('b', {'dependencies': ['a'],
                'payload': {'onExitStatus': {'retry': [1]}},
                'provisionerId': 'aws-provisioner-v1'})])
    assert graph_to_tasks(graph) == expected


def test_graph_to_tasks_exit_status_2():
    graph = {
        "tasks": [
            {
                "requires": ["a"],
                "taskId": "b",
                "task": {"payload": {'onExitStatus': {'retry': [2, 3, 45]}},
                         "provisionerId": "aws-provisioner-v1"}
            }
        ]
    }
    expected = OrderedDict(
        [('b', {'dependencies': ['a'],
                'payload': {'onExitStatus': {'retry': [2, 3, 45]}},
                'provisionerId': 'aws-provisioner-v1'})])
    assert graph_to_tasks(graph) == expected


def test_graph_to_tasks_no_requires():
    graph = {
        "tasks": [
            {
                "taskId": "b",
                "task": {"payload": {}, "provisionerId": "m"}
            }
        ]
    }
    expected = OrderedDict(
        [('b', {'payload': {}, 'provisionerId': 'm'})])
    assert graph_to_tasks(graph) == expected


def test_graph_to_tasks_multiple():
    graph = {
        "tasks": [
            {
                "requires": ["b"],
                "taskId": "a",
                "task": {"payload": {}, "provisionerId": "m"}
            },
            {
                "requires": ["c"],
                "taskId": "b",
                "task": {"payload": {}, "provisionerId": "m"}
            },
            {
                "taskId": "c",
                "task": {"payload": {}, "provisionerId": "m"}
            },
        ]
    }
    expected = OrderedDict([
        ('a', {'dependencies': ['b'], 'payload': {}, 'provisionerId': 'm'}),
        ('b', {'dependencies': ['c'], 'payload': {}, 'provisionerId': 'm'}),
        ('c', {'payload': {}, 'provisionerId': 'm'})])
    assert graph_to_tasks(graph) == expected


def test_add_atomic_task():
    initial = OrderedDict([
        ('a', {'dependencies': ['b'], 'payload': {}, 'provisionerId': 'm'}),
        ('b', {'dependencies': ['c'], 'payload': {}, 'provisionerId': 'm'}),
        ('c', {'payload': {}, 'provisionerId': 'm'})])

    expected = OrderedDict([
        ('a', {'dependencies': ['b'], 'payload': {}, 'provisionerId': 'm'}),
        ('b', {'dependencies': ['c'], 'payload': {}, 'provisionerId': 'm'}),
        ('c', {'dependencies': ['z'], 'payload': {}, 'provisionerId': 'm'}),
        ('z', {'payload': 'z task'})])
    assert add_atomic_task(initial, ("z", {"payload": "z task"})) == expected


def test_inject_dummy_tasks():
    before = OrderedDict([
        ('a', {'dependencies': ['b', 'c', 'd'], 'payload': {},
               'provisionerId': 'm'}),
    ])
    after = inject_dummy_tasks(before, {"payload": "meh"}, max_deps=2)
    assert len(after) == 3
