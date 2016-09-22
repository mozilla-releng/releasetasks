import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE, create_test_args


class TestChecksums(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        test_kwargs = create_test_args({
            'push_to_candidates_enabled': True,
            'checksums_enabled': True,
            'updates_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'en_US_config': {
                "platforms": {
                    "macosx64": {"task_id": "abc"},
                    "win64": {"task_id": "jgh"},
                    "linux64": {"task_id": "lmn"},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-firefox_chcksms")
        self.payload = self.task["task"]["payload"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"], "buildbot-bridge")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "buildbot-bridge")

    def test_scopes_present(self):
        self.assertFalse("scopes" in self.task)

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))

    def test_version(self):
        self.assertEqual(self.payload["properties"]["version"], "42.0b2")

    def test_build_number(self):
        self.assertEqual(self.payload["properties"]["build_number"], "3")

    def test_requires(self):
        tmpl = "release-foo_firefox_{p}_complete_en-US_beetmover_candidates"
        tmpl_partials = "release-foo_firefox_{p}_partial_en-US_{v}build{b}_beetmover_candidates"
        requires = [
            get_task_by_name(self.graph, tmpl.format(p=p))["taskId"]
            for p in ("linux64", "macosx64", "win64")
        ] + [
            get_task_by_name(self.graph, tmpl_partials.format(p=p, v=v, b=b))["taskId"]
            for p in ("linux64", "macosx64", "win64")
            for v, b in [("37.0", 2), ("38.0", 1)]
        ]
        self.assertEqual(sorted(self.task["requires"]), sorted(requires))
