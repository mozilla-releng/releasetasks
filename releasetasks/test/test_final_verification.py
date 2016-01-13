import unittest

from releasetasks.test import make_task_graph, PVT_KEY_FILE, \
    do_common_assertions, get_task_by_name


class TestFinalVerification(unittest.TestCase):
    """Because of how huge the graph gets, verifying every character of it is
    impossible to maintain. Instead, we verify aspects of it. Eg, making sure
    the correct number of funsize partials are happening, rather than verifying
    the entire funsize tasks."""
    maxDiff = 30000

    def test_final_verify_task_definition(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            en_US_config={"platforms": {
                "linux": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
            l10n_config={},
            repo_path="releases/foo",
            revision="fedcba654321",
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=False,
            product="firefox",
            signing_class="release-signing",
            release_channels=["foo"],
            enUS_platforms=["linux", "linux64", "win64", "win32", "macosx64"],
            signing_pvt_key=PVT_KEY_FILE,
        )
        do_common_assertions(graph)

        task_def = get_task_by_name(graph, "foo_final_verify")
        task = task_def["task"]
        payload = task["payload"]
        self.assertEqual(task["provisionerId"], "aws-provisioner-v1")
        self.assertEqual(task["workerType"], "b2gtest")
        self.assertFalse("scopes" in task)
        # XXX: Change the image name once it's in-tree.
        self.assertTrue(payload["image"].startswith("rail/python-test-runner"))
        self.assertFalse("cache" in payload)
        self.assertFalse("artifacts" in payload)
        self.assertTrue("env" in payload)
        self.assertTrue("command" in payload)

        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(graph["scopes"]))


class TestFinalVerificationMultiChannel(unittest.TestCase):
    """Because of how huge the graph gets, verifying every character of it is
    impossible to maintain. Instead, we verify aspects of it. Eg, making sure
    the correct number of funsize partials are happening, rather than verifying
    the entire funsize tasks."""
    maxDiff = 30000

    def test_multi_channel_final_verify_task_definition(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            en_US_config={"platforms": {
                "linux": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
            l10n_config={},
            repo_path="releases/foo",
            revision="fedcba654321",
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=False,
            product="firefox",
            signing_class="release-signing",
            release_channels=["beta", "release"],
            enUS_platforms=["linux", "linux64", "win64", "win32", "macosx64"],
            signing_pvt_key=PVT_KEY_FILE,
        )
        do_common_assertions(graph)

        for chan in ["beta", "release"]:
            task_def = get_task_by_name(graph,
                                        "{chan}_final_verify".format(chan=chan))
            task = task_def["task"]
            payload = task["payload"]
            self.assertEqual(task["provisionerId"], "aws-provisioner-v1")
            self.assertEqual(task["workerType"], "b2gtest")
            self.assertFalse("scopes" in task)
            # XXX: Change the image name once it's in-tree.
            self.assertTrue(payload["image"].startswith("rail/python-test-runner"))
            self.assertFalse("cache" in payload)
            self.assertFalse("artifacts" in payload)
            self.assertTrue("env" in payload)
            self.assertTrue("command" in payload)

            expected_graph_scopes = set([
                "queue:task-priority:high",
            ])
            self.assertTrue(expected_graph_scopes.issubset(graph["scopes"]))
