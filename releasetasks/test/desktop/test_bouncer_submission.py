import unittest

from releasetasks.test.desktop import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
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
                        'partial_versions': ', '.join([
                            '37.0build2',
                            '38.0build1',
                        ]),
                    }
                }
            }
        }, required=True, extra=True)

        test_kwargs = create_firefox_test_args({
            'bouncer_enabled': True,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': {
                "platforms": {
                    "macosx64": {},
                    "win32": {},
                    "win64": {},
                    "linux": {},
                    "linux64": {},
                }
            },
        })

        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo_firefox_bncr_sub")

    @staticmethod
    @truth
    def not_allowed(task):
        return "scopes" not in task

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_bouncer_submission_task(self):
        verify(self.task, self.task_schema, TestBouncerSubmission.not_allowed)
