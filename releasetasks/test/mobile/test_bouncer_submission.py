import unittest

from releasetasks.test.mobile import make_task_graph, do_common_assertions, \
    get_task_by_name, create_fennec_test_args
from releasetasks.test import PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestBouncerSubmission(unittest.TestCase):
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
                        'build_number': 3,
                        'repo_path': 'releases/foo',
                        'script_repo_revision': 'abcd',
                    }
                }
            }
        }, required=True, extra=True)

        test_kwargs = create_fennec_test_args({
            'bouncer_enabled': True,
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
        self.task = get_task_by_name(self.graph, "release-foo-fennec_bncr_sub")

    @staticmethod
    @truth
    def not_allowed(task):
        return "scopes" not in task

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_bouncer_submission_task(self):
        verify(self.task, self.task_schema, TestBouncerSubmission.not_allowed)
