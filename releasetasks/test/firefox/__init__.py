# -*- coding: utf-8 -*-
import mock
from jose import jwt
from jose.constants import ALGORITHMS
import os
import yaml

from releasetasks import make_task_graph as make_task_graph_orig
from releasetasks.test import PUB_KEY, DUMMY_PUBLIC_KEY, verify
from voluptuous import All, Any, Optional, Schema, truth


@truth
def passes_task_provisionerId_test(task):
    if task['provisionerId'] == "buildbot-bridge":
        assert not {"treeherderEnv", "treeherderEnv"}.intersection(task["extra"])
        assert not any([r.startswith("tc-treeherder") for r in task["routes"]])

    if task['provisionerId'] == "aws-provisioner-v1":
        assert {"treeherder", "treeherderEnv"}.intersection(task["extra"])
        assert len([r for r in task["routes"] if r.startswith("tc-treeherder")]) == 2
    return True  # if this line is reached the test passes


@truth
def passes_task_signature_test(task):
    assert task['taskId'] == jwt.decode(task['task']["extra"]["signing"]["signature"], PUB_KEY, algorithms=[ALGORITHMS.RS512])['taskId']
    return True


@truth
def passes_index_route_requirement(task_routes):
    rel_routes = [r.startswith("index.releases.") for r in task_routes]
    assert len(rel_routes) >= 2, "At least 2 release index routes required"
    return True


COMMON_TASK_SCHEMA = Schema(All(passes_task_signature_test, {  # Must pass task signature test, and the below Schema
    'reruns': int,
    'taskId': str,
    'task': All(passes_task_provisionerId_test,  # Must pass provisionerId test, and the below Schema
                Schema({
                    'routes': passes_index_route_requirement,
                    'priority': 'high',
                    'metadata': {
                        'name': str,
                    },
                    'extra': {
                        'task_name': str,
                        'build_props': {
                            'product': str,
                            'locales': Any([str], [None]),
                            'branch': str,
                            'platform': Any(str, None),
                            'version': str,
                            'revision': str,
                            'build_number': int,
                        },
                        'signing': {
                            'signature': str,
                        }
                    },
                    'payload': {
                        Optional('properties'): {
                            'version': str,
                            'build_number': int,
                            'release_promotion': bool,
                            'revision': str,
                            'product': str,
                        }
                    },
                }, extra=True, required=True))
}, extra=True, required=True))


def create_firefox_test_args(non_standard_arguments):
    with open(os.path.join(os.path.dirname(__file__), 'default_graph_parameters.yml')) as f:
        default_arguments = yaml.safe_load(f)
    default_arguments.update(non_standard_arguments)
    return default_arguments


def do_common_assertions(graph):
    _cached_taskIDs = set()
    if graph['tasks']:
        for t in graph['tasks']:
            assert t['taskId'] not in _cached_taskIDs
            verify(t, COMMON_TASK_SCHEMA)

            _cached_taskIDs.add(t['taskId'])


def get_task_by_name(graph, name):
    for t in graph["tasks"]:
        if t["task"]["extra"]["task_name"] == name:
            return t
    return None


@mock.patch("releasetasks.get_json_rev")
def make_task_graph(*args, **kwargs):
    args = list(args)
    mocked_get_json_rev = args.pop()
    mocked_get_json_rev.return_value = {"pushid": 78123}
    return make_task_graph_orig(*args, public_key=DUMMY_PUBLIC_KEY,
                                balrog_username="fake", balrog_password="fake",
                                beetmover_aws_access_key_id="baz",
                                beetmover_aws_secret_access_key="norf",
                                running_tests=True, **kwargs)
