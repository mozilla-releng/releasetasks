# -*- coding: utf-8 -*-
import mock
from jose import jwt
from jose.constants import ALGORITHMS
import os
import yaml

from releasetasks import make_task_graph as make_task_graph_orig
from releasetasks.test import PUB_KEY, DUMMY_PUBLIC_KEY, verify
from voluptuous import All, Any, Email, Extra, Length, Match, Optional, Range, Required, Schema, truth, Unique, Url

TASKCLUSTER_ID_REGEX = r'^[A-Za-z0-9_-]{8}[Q-T][A-Za-z0-9_-][CGKOSWaeimquy26-][A-Za-z0-9_-]{10}[AQgw]$'


@truth
def unique_task_ids(graph):
    """Test the graph generates all unique task IDs"""
    set_of_task_ids = set()
    if graph['tasks']:
        for task in graph['tasks']:
            if task['taskId'] in set_of_task_ids:
                return False
            else:
                set_of_task_ids.add(task['taskId'])

    return True


@truth
def task_provisionerId_test(task):
    """Test the provisionerId requirements are met"""
    if task['provisionerId'] == "buildbot-bridge":
        return not {"treeherderEnv", "treeherderEnv"}.intersection(task["extra"]) and not any([r.startswith("tc-treeherder") for r in task["routes"]])

    if task['provisionerId'] == "aws-provisioner-v1":
        return {"treeherder", "treeherderEnv"}.intersection(task["extra"]) and len([r for r in task["routes"] if r.startswith("tc-treeherder")]) == 2

    return True


@truth
def task_signature_test(task):
    """Test the task signatures are generated as expected."""
    return task['taskId'] == jwt.decode(task['task']["extra"]["signing"]["signature"], PUB_KEY, algorithms=[ALGORITHMS.RS512])['taskId']


@truth
def index_route_requirement(task_routes):
    rel_routes = [r.startswith("index.releases.") for r in task_routes]
    return len(rel_routes) >= 2


COMMON_TASK_SCHEMA = Schema(All(task_signature_test, {  # Must pass task signature test, and the below Schema
    'requires': Any([Match(TASKCLUSTER_ID_REGEX)], None),
    Required('reruns', msg="Required for releasetasks schema."): Range(min=0, max=100),
    Required('taskId', msg="Required for TaskCluster schema."): Match(TASKCLUSTER_ID_REGEX),
    Required('task', msg="Required for TaskCluster schema."): All(task_provisionerId_test, Schema({
                    Required('created', msg="Required for TaskCluster schema."): str,
                    Required('deadline', msg="Required for TaskCluster schema."): str,
                    Required('extra', msg="Required for releasetasks schema."): {
                        'task_name': str,
                        'build_props': {
                            'product': str,
                            'locales': Any([str], [None]),
                            'branch': str,
                            'platform': Any(str, None),
                            'version': str,
                            'revision': str,
                            'build_number': int,
                            Extra: object,
                        },
                        'signing': {
                            'signature': str,
                        },
                        Extra: object,
                    },
                    Required('metadata', msg="Required for TaskCluster schema."): {
                        'name': All(str, Length(max=255)),
                        'description': All(str, Length(max=32768)),
                        'owner': All(Email(), Length(max=255)),
                        'source': All(Url(), Length(max=4096)),
                    },
                    Required('payload', msg="Required for TaskCluster schema."): {
                        Extra: object,
                        Optional('properties'): {
                            'version': str,
                            'build_number': int,
                            'release_promotion': bool,
                            'revision': str,
                            'product': str,
                            Extra: object,
                        }
                    },
                    Required('provisionerId', msg="Required for TaskCluster schema."): All(Match(r'^([a-zA-Z0-9-_]*)$'), Length(min=1, max=22)),
                    Required('priority', msg="Required for releasetasks schema."): 'high',
                    Required('routes', msg="Required for releasetasks schema."): All(
                        [All(str, Length(min=1, max=249))],
                        index_route_requirement,
                        Length(max=10),
                        Unique(),
                        msg="Maximum 10 unique routes per task."),
                    Required('workerType', msg="Required for TaskCluster schema."): All(Match(r'^([a-zA-Z0-9-_]*)$'), Length(min=1, max=22)),
                    'dependencies': All([Match(TASKCLUSTER_ID_REGEX)],
                                        Length(max=100),
                                        Unique()),
                    'expires': str,
                    'requires': Any('all-completed', 'all-resolved'),
                    'retries': Range(min=0, max=49),
                    'schedulerId': All(Match(r'^([a-zA-Z0-9-_]*)$'), Length(min=1, max=22)),
                    'scopes': [Match(r'^[\x20-\x7e]*$')],
                    'tags': {
                        All(str, Length(max=4096)): str,
                    },
                    'taskGroupId': Match(TASKCLUSTER_ID_REGEX),
                }, extra=False, required=False))
}, extra=False, required=False))

TC_GRAPH_SCHEMA = Schema({
    Required('tasks', msg="Required for TaskCluster schema."): Any([COMMON_TASK_SCHEMA], None),
    Required('metadata', msg="Required for TaskCluster schema."): Schema({
        'name': All(str, Length(max=255)),
        'description': All(str, Length(max=32768)),
        'owner': All(Email(), Length(max=255)),
        'source': All(Url(), Length(max=4096))
    }, extra=False, required=True),
    'scopes': [str],
    'routes': All(
        [All(str, Length(min=1, max=249))],
        Unique(),
        Length(max=10)
    ),
    'tags': {
        All(str, Length(max=4096)): str,
    },
}, extra=False, required=False)


def create_fennec_test_args(non_standard_arguments):
    with open(os.path.join(os.path.dirname(__file__), 'default_graph_parameters.yml')) as f:
        default_arguments = yaml.safe_load(f)
    default_arguments.update(non_standard_arguments)
    return default_arguments


def do_common_assertions(graph):
    verify(graph, TC_GRAPH_SCHEMA, unique_task_ids)


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
