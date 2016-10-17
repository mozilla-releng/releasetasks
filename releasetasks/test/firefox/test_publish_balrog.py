import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE
from voluptuous import Schema
from voluptuous.humanize import validate_with_humanized_errors


class TestPublishBalrog(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    TASK_SCHEMA = Schema({
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

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'publish_to_balrog_channels': ["release-dev", "alpha"],
            'en_US_config': {
                "platforms": {
                    "macosx64": {"task_id": "abc"},
                    "win32": {"task_id": "def"},
                    "win64": {"task_id": "jgh"},
                    "linux": {"task_id": "ijk"},
                    "linux64": {"task_id": "lmn"},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-firefox_publish_balrog")

    def test_publish_balrog_task(self):
        assert validate_with_humanized_errors(self.task, TestPublishBalrog.TASK_SCHEMA)

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_requires(self):
        requires = [get_task_by_name(self.graph, "publish_release_human_decision")["taskId"]]
        self.assertEqual(sorted(self.task["requires"]), sorted(requires))
