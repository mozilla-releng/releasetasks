import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE, create_test_args


class TestPublishBalrog(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        test_kwargs = create_test_args({
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
        self.payload = self.task["task"]["payload"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"],
                         "buildbot-bridge")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "buildbot-bridge")

    def test_requires(self):
        requires = [get_task_by_name(self.graph, "publish_release_human_decision")["taskId"]]
        self.assertEqual(sorted(self.task["requires"]), sorted(requires))

    def test_balrog_api(self):
        self.assertEqual(self.payload["properties"]["balrog_api_root"],
                         "https://balrog.real/api")

    def test_channels(self):
        self.assertEqual(self.payload["properties"]["channels"],
                         "alpha, release-dev")
