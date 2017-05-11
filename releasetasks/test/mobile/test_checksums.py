import unittest

from releasetasks.test.mobile import make_task_graph, do_common_assertions, \
    get_task_by_name, create_fennec_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestChecksums(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={'queue:task-priority:high'}),
        }, extra=True, required=True)

        self.test_schema = Schema({
            'task': {
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'properties': {
                        'version': '42.0b2',
                        'build_number': 3,
                    }
                }
            }
        }, extra=True, required=True)

        test_kwargs = create_fennec_test_args({
            'push_to_candidates_enabled': True,
            'checksums_enabled': True,
            'updates_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'en_US_config': {
                "platforms": {
                    "android-4-0-armv7-api15": {"task_id": "abc"},
                    "android-4-2-x86": {"task_id": "lmn"},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-fennec_chcksms")

    @staticmethod
    @truth
    def not_allowed(task):
        return 'scopes' not in task

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_graph(self):
        verify(self.graph, self.graph_schema)
