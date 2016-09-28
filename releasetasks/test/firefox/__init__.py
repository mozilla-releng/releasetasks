# -*- coding: utf-8 -*-
import mock
from jose import jwt
from jose.constants import ALGORITHMS
import os
import yaml

from releasetasks import make_task_graph as make_task_graph_orig
from releasetasks.test import PUB_KEY, DUMMY_PUBLIC_KEY
from voluptuous import All, Any, Optional, Required, Schema, truth
from voluptuous.humanize import validate_with_humanized_errors


@truth
def passes_task_provisionerId_test(task):
    if task['provisionerId'] == "buildbot-bridge":
        assert not {"treeherderEnv", "treeherderEnv"}.intersection(task["extra"])
        assert not any([r.startswith("tc-treeherder") for r in task["routes"]])

    if task['provisionerId'] == "aws-provisioner-v1":
        assert {"treeherder", "treeherderEnv"}.intersection(task["extra"])
        assert len([r for r in task["routes"] if r.startswith("tc-treeherder")]) == 2
    return True  # if this line is reached the schema is validated


@truth
def passes_task_signature_test(task):
    assert task['task']['taskId'] == jwt.decode(task['task']["extra"]["signing"]["signature"], PUB_KEY, algorithms=[ALGORITHMS.RS512])['taskId']
    return True


@truth
def passes_index_route_requirement(task_routes):
    rel_routes = [r.startswith("index.releases.") for r in task_routes]
    assert len(rel_routes) >= 2, "At least 2 release index routes required"
    return True


TASK_SCHEMA = Schema(All({
    Required('reruns'): int,
    Required('taskId'): Any(int, str),
    Required('task'): All(
        Schema({
            Required('priority'): 'high',
            Required('metadata'): {
                Required('name'): str,
            },
            Required('extra'): {
                Required('task_name'): str,
                Required('build_props'): {
                    Required('product'): str,
                    Required('locales'): Any([str], [None]),
                    Required('branch'): str,
                    Required('platform'): Any(str, None),
                    Required('version'): str,
                    Required('revision'): str,
                    Required('build_number'): int,
                },
                Required('signing'): {
                    Required('signature'): str,
                }
            },
            Required('payload'): {
                Optional('properties'): {
                    Required('version'): str,
                    Required('build_number'): Any(str, int),  # TODO: ask rail about this being string/int, or set in specific test
                    Required('release_promotion'): bool,
                    Required('revision'): str,
                    Required('product'): str,
                }
            },
            Required('routes'): passes_index_route_requirement,
        }, extra=True), passes_task_provisionerId_test)
}, extra=True), passes_task_signature_test)


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
            assert t == validate_with_humanized_errors(t, TASK_SCHEMA)

            _cached_taskIDs.add(t['taskId'])


def verify(graph, schema):
    _cached_task_ids = set()
    if graph['tasks']:
        test_schema = TASK_SCHEMA.update(schema)
        for t in graph['tasks']:
            assert t == validate_with_humanized_errors(test_schema(t))
            assert t['taskId'] not in _cached_task_ids
            _cached_task_ids.add(t['taskId'])


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
