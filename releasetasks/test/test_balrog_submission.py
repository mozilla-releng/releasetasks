import unittest

from releasetasks.test import make_task_graph, PVT_KEY_FILE, \
    do_common_assertions, get_task_by_name


class TestBalrogSubmission(unittest.TestCase):
    """Because of how huge the graph gets, verifying every character of it is
    impossible to maintain. Instead, we verify aspects of it. Eg, making sure
    the correct number of funsize partials are happening, rather than verifying
    the entire funsize tasks."""
    maxDiff = 30000

    def test_bouncer_submission_task_definition(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            l10n_config={},
            repo_path="releases/foo",
            product="firefox",
            revision="fedcba654321",
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=True,
            signing_class="release-signing",
            release_channels=["foo"],
            enUS_platforms=["linux", "linux64", "win64", "win32", "macosx64"],
            signing_pvt_key=PVT_KEY_FILE,
        )
        do_common_assertions(graph)

        task = get_task_by_name(graph, "release-foo_firefox_bncr_sub")

        payload = task["task"]["payload"]

        self.assertEqual(task["task"]["provisionerId"], "buildbot-bridge")
        self.assertEqual(task["task"]["workerType"], "buildbot-bridge")
        self.assertFalse("scopes" in task)
        # XXX: Change the image name once it's in-tree.
        self.assertEqual(payload["properties"]["partial_versions"], "37.0, 38.0,")
        self.assertEqual(payload["properties"]["build_number"], 3)

        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(graph["scopes"]))
