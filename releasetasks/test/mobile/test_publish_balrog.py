import unittest

from releasetasks.test.mobile import (make_task_graph, do_common_assertions,
                                      get_task_by_name, create_fennec_test_args)
from releasetasks.test import PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestPublishBalrog(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'properties': {
                        'balrog_api_root': 'https://balrog.real/api',
                        'channels': 'alpha, release-dev',
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
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'publish_to_balrog_channels': ["release-dev", "alpha"],
            'en_US_config': {
                "platforms": {
                    "android-4-0-armv7-api15": {"task_id": "abc"},
                    "android-4-2-x86": {"task_id": "def"},
                }
            },
        })

        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-fennec_publish_balrog")
        self.push_to_mirrors = get_task_by_name(self.graph, "release-foo-fennec_push_to_releases")

    def generate_task_requires_validator(self):
        push_to_mirrors_task_id = self.push_to_mirrors['taskId']

        @truth
        def validate_task_dependencies(task):
            return push_to_mirrors_task_id in task['requires']

        return validate_task_dependencies

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_publish_balrog_task(self):
        verify(self.task, self.task_schema, self.generate_task_requires_validator())

    def test_push_to_mirrors(self):
        verify(self.push_to_mirrors, self.push_to_mirrors_schema)
