import unittest

from releasetasks.test.mobile import (make_task_graph, do_common_assertions,
                                      get_task_by_name, create_fennec_test_args)
from releasetasks.test import PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestUptakeMonitoring(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'scopes': list,
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'properties': {
                        'product': 'fennec',
                        'version': '42.0b2',
                        'build_number': 3,
                        'repo_path': 'releases/foo',
                        'script_repo_revision': 'abcd',
                        'revision': 'abcdef123456',
                        'tuxedo_server_url': 'https://bouncer.real.allizom.org/api',
                    }
                }
            }
        }, extra=True, required=True)

        test_kwargs = create_fennec_test_args({
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'uptake_monitoring_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'uptake_monitoring_platforms': ["android-4-0-armv7-api15", "android-4-2-x86"],
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'en_US_config': {
                "platforms": {
                    "android-4-0-armv7-api15": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
                    "android-4-2-x86": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-fennec_uptake_monitoring")
        self.payload = self.task["task"]["payload"]

    def generate_task_dependency_validator(self):
        requires = sorted([get_task_by_name(self.graph, "release-foo-fennec_push_to_releases")["taskId"]])

        @truth
        def validate_task_dependencies(task):
            return sorted(requires) == sorted(task['requires'])

        return validate_task_dependencies

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_uptake_monitoring_task(self):
        verify(self.task, self.task_schema, self.generate_task_dependency_validator())
