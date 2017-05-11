import unittest

from releasetasks.test.mobile import (make_task_graph, do_common_assertions,
                                      get_task_by_name, create_fennec_test_args)
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestVersionBump(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    human_task = None
    payload = None

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={
                "queue:task-priority:high",
            })
        }, extra=True, required=True)

        self.task_schema = Schema({
            'task': {
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'properties': {
                        'next_version': '42.0b3',
                        'repo_path': 'releases/foo',
                        'script_repo_revision': 'abcd',
                    }
                }
            }
        }, extra=True, required=True)

        self.push_to_mirrors_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'gecko-3-b-linux',
            }
        }, extra=True, required=True)

        test_kwargs = create_fennec_test_args({
            'push_to_releases_enabled': True,
            'bouncer_enabled': True,
            'postrelease_version_bump_enabled': True,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': {
                "platforms": {
                    "android-4-0-armv7-api15": {"task_id": "abc"},
                    "android-4-2-x86": {"task_id": "def"},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-fennec_version_bump")
        self.push_to_mirrors = get_task_by_name(self.graph, "release-foo-fennec_push_to_releases")

    def generate_task_dependency_validator(self):
        push_to_mirrors_task_id = self.push_to_mirrors['taskId']

        @truth
        def validate_task_dependencies(task):
            return push_to_mirrors_task_id in task['requires']

        return validate_task_dependencies

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_push_to_mirrors(self):
        verify(self.push_to_mirrors, self.push_to_mirrors_schema)

    def test_version_bump_task(self):
        verify(self.task, self.task_schema, self.generate_task_dependency_validator())
